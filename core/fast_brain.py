"""Run a trained brain with NumPy only, so the public server needs no PyTorch (Vercel caps a function at 500 MB).

Reads the same models/*.pt files the trainer writes. torch.save writes a zip holding a pickle plus the raw
tensor bytes; a strict unpickler that knows only tensors and plain containers turns them into NumPy arrays.
The forward pass mirrors core/neural_net.NexusBrain exactly (pre-LayerNorm encoder, masked mean pooling).
"""
import collections
import math
import pickle
import zipfile
from pathlib import Path

import numpy as np

_STORAGE = {"FloatStorage": np.float32, "HalfStorage": np.float16, "DoubleStorage": np.float64,
            "LongStorage": np.int64, "IntStorage": np.int32, "BoolStorage": np.bool_, "ByteStorage": np.uint8}


def _rebuild_tensor(storage, offset, size, stride, *_):
    item = storage.itemsize
    return np.lib.stride_tricks.as_strided(storage[offset:], shape=tuple(size),
                                           strides=tuple(s * item for s in stride)).copy()


def load_checkpoint(path: Path) -> dict:
    """torch.load(path, weights_only=True) without torch: tensors come back as NumPy arrays."""
    with zipfile.ZipFile(path) as z:
        root = z.namelist()[0].split("/")[0]

        class Reader(pickle.Unpickler):
            def find_class(self, module, name):
                if module == "torch._utils" and name == "_rebuild_tensor_v2":
                    return _rebuild_tensor
                if module == "torch" and name in _STORAGE:
                    return _STORAGE[name]
                if module == "collections" and name == "OrderedDict":
                    return collections.OrderedDict
                raise pickle.UnpicklingError(f"not allowed in a checkpoint: {module}.{name}")

            def persistent_load(self, pid):  # ("storage", dtype, key, location, numel)
                _, dtype, key, _, numel = pid
                return np.frombuffer(z.read(f"{root}/data/{key}"), dtype=dtype, count=numel)

        with z.open(f"{root}/data.pkl") as f:
            return Reader(f).load()


def _layer_norm(x: np.ndarray, w: np.ndarray, b: np.ndarray) -> np.ndarray:
    mean = x.mean(-1, keepdims=True)
    return (x - mean) / np.sqrt(x.var(-1, keepdims=True) + 1e-5) * w + b


def _gelu(x: np.ndarray) -> np.ndarray:
    """Exact GELU, 0.5·x·(1 + erf(x/√2)), with erf from Abramowitz & Stegun 7.1.26 (error < 1.5e-7)."""
    z = x / math.sqrt(2.0)
    t = 1.0 / (1.0 + 0.3275911 * np.abs(z))
    poly = t * (0.254829592 + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429))))
    erf = np.sign(z) * (1.0 - poly * np.exp(-z * z))
    return 0.5 * x * (1.0 + erf)


class NumpyBrain:
    """Same maths as NexusBrain.forward for one sentence; returns the class logits."""

    def __init__(self, config: dict, state: dict):
        self.config = config
        self.w = {k: np.asarray(v, dtype=np.float32) for k, v in state.items()}
        if "pos.pe" not in self.w:  # older checkpoints: rebuild the fixed sinusoidal table
            d, n = config["d_model"], config["max_len"]
            pos = np.arange(n, dtype=np.float32)[:, None]
            div = np.exp(np.arange(0, d, 2, dtype=np.float32) * (-math.log(10000.0) / d))
            pe = np.zeros((n, d), dtype=np.float32)
            pe[:, 0::2], pe[:, 1::2] = np.sin(pos * div), np.cos(pos * div)
            self.w["pos.pe"] = pe[None]

    def params(self) -> int:
        return sum(v.size for k, v in self.w.items() if k != "pos.pe")

    def _linear(self, x: np.ndarray, name: str) -> np.ndarray:
        return x @ self.w[name + ".weight"].T + self.w[name + ".bias"]

    def _attention(self, x: np.ndarray, pad: np.ndarray, prefix: str) -> np.ndarray:
        t, d = x.shape
        heads = self.config["n_heads"]
        q, k, v = self._linear(x, prefix + "qkv").reshape(t, 3, heads, d // heads).transpose(1, 2, 0, 3)
        scores = q @ k.transpose(0, 2, 1) / math.sqrt(d // heads)
        scores[:, :, pad] = -np.inf  # never attend to padding
        scores = np.exp(scores - scores.max(-1, keepdims=True))
        scores /= scores.sum(-1, keepdims=True)
        ctx = (scores @ v).transpose(1, 0, 2).reshape(t, d)
        return self._linear(ctx, prefix + "out")

    def __call__(self, ids: list[int]) -> np.ndarray:
        w, cfg = self.w, self.config
        ids = np.asarray(ids, dtype=np.int64)
        pad = ids == cfg["pad_id"]
        x = w["embed.weight"][ids] * math.sqrt(cfg["d_model"]) + w["pos.pe"][0, :len(ids)]
        for i in range(cfg["n_layers"]):
            p = f"blocks.{i}."
            x = x + self._attention(_layer_norm(x, w[p + "ln1.weight"], w[p + "ln1.bias"]), pad, p + "attn.")
            h = _gelu(self._linear(_layer_norm(x, w[p + "ln2.weight"], w[p + "ln2.bias"]), p + "ff.net.0"))
            x = x + self._linear(h, p + "ff.net.3")
        x = _layer_norm(x, w["ln_final.weight"], w["ln_final.bias"])
        keep = ~pad
        pooled = x[keep].sum(0) / max(int(keep.sum()), 1)
        return self._linear(pooled, "head")
