"""SADAH brain: a compact Transformer encoder built from scratch for intent routing."""
import math

import torch
import torch.nn as nn
import torch.nn.functional as F


class PositionalEncoding(nn.Module):
    """Fixed sinusoidal positional encoding (Vaswani et al., 2017)."""

    def __init__(self, d_model: int, max_len: int = 128):
        super().__init__()
        pos = torch.arange(max_len).unsqueeze(1)
        div = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        pe = torch.zeros(max_len, d_model)
        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, : x.size(1)]


class MultiHeadSelfAttention(nn.Module):
    def __init__(self, d_model: int, n_heads: int, dropout: float = 0.1):
        super().__init__()
        assert d_model % n_heads == 0, "d_model must be divisible by n_heads"
        self.n_heads, self.d_head = n_heads, d_model // n_heads
        self.qkv = nn.Linear(d_model, 3 * d_model)
        self.out = nn.Linear(d_model, d_model)
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, pad_mask: torch.Tensor) -> torch.Tensor:
        b, t, d = x.shape
        q, k, v = self.qkv(x).view(b, t, 3, self.n_heads, self.d_head).permute(2, 0, 3, 1, 4)
        scores = q @ k.transpose(-2, -1) / math.sqrt(self.d_head)
        # pad_mask: (b, t) True where padding -> never attend to those keys
        scores = scores.masked_fill(pad_mask[:, None, None, :], float("-inf"))
        attn = self.drop(F.softmax(scores, dim=-1))
        ctx = (attn @ v).transpose(1, 2).reshape(b, t, d)
        return self.out(ctx)


class FeedForward(nn.Module):
    def __init__(self, d_model: int, d_ff: int, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, d_ff), nn.GELU(), nn.Dropout(dropout), nn.Linear(d_ff, d_model)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class EncoderBlock(nn.Module):
    """Pre-LayerNorm transformer block: x + Attn(LN(x)), then x + FF(LN(x))."""

    def __init__(self, d_model: int, n_heads: int, d_ff: int, dropout: float):
        super().__init__()
        self.ln1, self.ln2 = nn.LayerNorm(d_model), nn.LayerNorm(d_model)
        self.attn = MultiHeadSelfAttention(d_model, n_heads, dropout)
        self.ff = FeedForward(d_model, d_ff, dropout)
        self.drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, pad_mask: torch.Tensor) -> torch.Tensor:
        x = x + self.drop(self.attn(self.ln1(x), pad_mask))
        return x + self.drop(self.ff(self.ln2(x)))


class SadahBrain(nn.Module):
    def __init__(self, vocab_size: int, n_classes: int, d_model: int = 64, n_heads: int = 4,
                 n_layers: int = 2, d_ff: int = 128, max_len: int = 32, dropout: float = 0.1,
                 pad_id: int = 0):
        super().__init__()
        self.pad_id = pad_id
        self.config = dict(vocab_size=vocab_size, n_classes=n_classes, d_model=d_model,
                           n_heads=n_heads, n_layers=n_layers, d_ff=d_ff, max_len=max_len,
                           dropout=dropout, pad_id=pad_id)
        self.embed = nn.Embedding(vocab_size, d_model, padding_idx=pad_id)
        self.pos = PositionalEncoding(d_model, max_len)
        self.blocks = nn.ModuleList(
            EncoderBlock(d_model, n_heads, d_ff, dropout) for _ in range(n_layers)
        )
        self.ln_final = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, n_classes)

    def encode(self, ids: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Contextual vector for every token (used by pre-training) plus the padding mask."""
        pad_mask = ids.eq(self.pad_id)
        x = self.pos(self.embed(ids) * math.sqrt(self.embed.embedding_dim))
        for block in self.blocks:
            x = block(x, pad_mask)
        return self.ln_final(x), pad_mask

    def forward(self, ids: torch.Tensor) -> torch.Tensor:
        x, pad_mask = self.encode(ids)
        # Masked mean pooling over real tokens.
        keep = (~pad_mask).unsqueeze(-1).float()
        pooled = (x * keep).sum(1) / keep.sum(1).clamp(min=1.0)
        return self.head(pooled)


class SadahMLM(nn.Module):
    """Self-supervised pre-training: predict hidden (masked) pieces from their context, like BERT.

    The encoder is a SadahBrain, so its weights transfer directly into the router/coder brains.
    The output layer reuses the input embedding matrix (weight tying), which saves parameters.
    """

    def __init__(self, **config):
        super().__init__()
        self.brain = SadahBrain(n_classes=1, **config)
        d = config.get("d_model", 64)
        self.transform = nn.Sequential(nn.Linear(d, d), nn.GELU(), nn.LayerNorm(d))
        self.bias = nn.Parameter(torch.zeros(config["vocab_size"]))
        # Embeddings are N(0, 1); without this 1/sqrt(d) the tied logits start ~16x too large (loss ≈ 45, not ≈ 9).
        self.scale = d ** -0.5

    def forward(self, ids: torch.Tensor) -> torch.Tensor:
        x, _ = self.brain.encode(ids)
        return (self.transform(x) @ self.brain.embed.weight.T) * self.scale + self.bias
