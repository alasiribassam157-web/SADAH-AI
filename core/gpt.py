"""SADAH generative brain: a decoder-only transformer trained from scratch (no external weights).

It writes text one token at a time.  Sizes (vocab 32k, context 512):
  small  d=512  layers 8   ≈ 42M      medium d=768 layers 12  ≈ 110M      large d=1024 layers 24 ≈ 350M
"""
import math

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint

SIZES = {
    "tiny": dict(d_model=128, n_layers=2, n_heads=4),        # CPU smoke test only
    "small": dict(d_model=512, n_layers=8, n_heads=8),
    "medium": dict(d_model=768, n_layers=12, n_heads=12),
    "large": dict(d_model=1024, n_layers=24, n_heads=16),
}


class Block(nn.Module):
    def __init__(self, d: int, heads: int, dropout: float):
        super().__init__()
        self.heads = heads
        self.ln1, self.ln2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.qkv = nn.Linear(d, 3 * d, bias=False)
        self.proj = nn.Linear(d, d, bias=False)
        self.mlp = nn.Sequential(nn.Linear(d, 4 * d, bias=False), nn.GELU(), nn.Linear(4 * d, d, bias=False))
        self.drop = nn.Dropout(dropout)
        self.p = dropout

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, t, d = x.shape
        q, k, v = self.qkv(self.ln1(x)).split(d, dim=2)
        q, k, v = (z.view(b, t, self.heads, d // self.heads).transpose(1, 2) for z in (q, k, v))
        # flash attention on GPU; causal = each token only sees the ones before it
        y = F.scaled_dot_product_attention(q, k, v, is_causal=True, dropout_p=self.p if self.training else 0.0)
        x = x + self.drop(self.proj(y.transpose(1, 2).reshape(b, t, d)))
        return x + self.drop(self.mlp(self.ln2(x)))


class SadahGPT(nn.Module):
    def __init__(self, vocab_size: int, d_model: int, n_layers: int, n_heads: int,
                 context: int = 512, dropout: float = 0.0, grad_checkpoint: bool = False):
        super().__init__()
        self.config = dict(vocab_size=vocab_size, d_model=d_model, n_layers=n_layers, n_heads=n_heads,
                           context=context, dropout=dropout)
        self.context = context
        self.grad_checkpoint = grad_checkpoint  # recompute activations during backward instead of storing them
        self.tok = nn.Embedding(vocab_size, d_model)
        self.pos = nn.Embedding(context, d_model)
        self.blocks = nn.ModuleList(Block(d_model, n_heads, dropout) for _ in range(n_layers))
        self.ln = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size, bias=False)
        self.head.weight = self.tok.weight  # tied: the same table reads and writes words
        self.apply(self._init)
        for name, p in self.named_parameters():  # GPT-2 style: scale residual projections by depth
            if name.endswith("proj.weight") or name.endswith("mlp.2.weight"):
                nn.init.normal_(p, std=0.02 / math.sqrt(2 * n_layers))

    @staticmethod
    def _init(m: nn.Module) -> None:
        if isinstance(m, (nn.Linear, nn.Embedding)):
            nn.init.normal_(m.weight, std=0.02)

    def params(self) -> int:
        return sum(p.numel() for p in self.parameters()) - self.pos.weight.numel()

    def forward(self, idx: torch.Tensor, targets: torch.Tensor | None = None):
        t = idx.size(1)
        x = self.tok(idx) + self.pos(torch.arange(t, device=idx.device))
        for block in self.blocks:
            # trades ~30% more compute for much less GPU memory — needed to fit "large" on a 16GB card
            x = checkpoint(block, x, use_reentrant=False) if self.grad_checkpoint and self.training else block(x)
        logits = self.head(self.ln(x))
        if targets is None:
            return logits, None
        loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1), ignore_index=-1)
        return logits, loss

    @torch.no_grad()
    def generate(self, idx: torch.Tensor, max_new: int = 120, temperature: float = 0.8, top_k: int = 40,
                 stop_id: int | None = None, repeat_penalty: float = 1.15) -> torch.Tensor:
        for _ in range(max_new):
            logits, _ = self(idx[:, -self.context:])
            logits = logits[:, -1, :] / max(temperature, 1e-5)
            for tok in set(idx[0, -64:].tolist()):  # discourage loops like «جدا جدا جدا»
                logits[0, tok] /= repeat_penalty if logits[0, tok] > 0 else 1 / repeat_penalty
            v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
            logits[logits < v[:, [-1]]] = -float("inf")
            nxt = torch.multinomial(F.softmax(logits, dim=-1), 1)
            idx = torch.cat([idx, nxt], dim=1)
            if stop_id is not None and nxt.item() == stop_id:
                break
        return idx
