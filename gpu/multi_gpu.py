"""Use every GPU on the machine (Kaggle T4 x2) with torchrun: one process per GPU, gradients averaged.

Started without torchrun (laptop smoke test, single GPU) everything here is a no-op.
"""
import os

import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP


def setup() -> tuple[bool, int, int, str]:
    """(is_ddp, rank, world_size, device) for this process."""
    if "RANK" not in os.environ:
        return False, 0, 1, "cuda" if torch.cuda.is_available() else "cpu"
    gpu = torch.cuda.is_available()
    dist.init_process_group("nccl" if gpu else "gloo")  # gloo = CPU, only for testing the pipeline
    local = int(os.environ["LOCAL_RANK"])
    if gpu:
        torch.cuda.set_device(local)
    return True, int(os.environ["RANK"]), int(os.environ["WORLD_SIZE"]), f"cuda:{local}" if gpu else "cpu"


def barrier(ddp: bool) -> None:
    if ddp:
        dist.barrier()


def wrap(model: torch.nn.Module, ddp: bool) -> torch.nn.Module:
    if not ddp:
        return model
    ids = [torch.cuda.current_device()] if torch.cuda.is_available() else None
    return DDP(model, device_ids=ids, broadcast_buffers=False)


def agree_stop(stop: bool, ddp: bool, device: str) -> bool:
    """GPU 0 decides when to stop, so all GPUs leave the loop on the same step (else they hang)."""
    if not ddp:
        return stop
    flag = torch.tensor([float(stop)], device=device)
    dist.broadcast(flag, 0)
    return bool(flag.item())


def finish(ddp: bool) -> None:
    if ddp:
        dist.destroy_process_group()
