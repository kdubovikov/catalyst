from typing import TYPE_CHECKING  # isort:skip

from catalyst.core import Callback, CallbackOrder

if TYPE_CHECKING:
    from catalyst.core import _State


class CheckRunCallback(Callback):
    def __init__(self, num_loader_steps: int = 1, num_epoch_steps: int = 1):
        super().__init__(CallbackOrder.External)
        self.num_loader_steps = num_loader_steps
        self.num_epoch_steps = num_epoch_steps

    def on_epoch_end(self, state: "_State"):
        if state.stage_epoch >= self.num_epoch_steps:
            state.need_early_stop = True

    def on_batch_end(self, state: "_State"):
        if state.loader_step >= self.num_loader_steps:
            state.need_early_stop = True


class EarlyStoppingCallback(Callback):
    def __init__(
        self,
        patience: int,
        metric: str = "loss",
        minimize: bool = True,
        min_delta: float = 1e-6
    ):
        super().__init__(CallbackOrder.External)
        self.best_score = None
        self.metric = metric
        self.patience = patience
        self.num_bad_epochs = 0
        self.is_better = None

        if minimize:
            self.is_better = lambda score, best: score <= (best - min_delta)
        else:
            self.is_better = lambda score, best: score >= (best + min_delta)

    def on_epoch_end(self, state: "_State") -> None:
        if state.stage_name.startswith("infer"):
            return

        score = state.valid_metrics[self.metric]
        if self.best_score is None:
            self.best_score = score
        if self.is_better(score, self.best_score):
            self.num_bad_epochs = 0
            self.best_score = score
        else:
            self.num_bad_epochs += 1

        if self.num_bad_epochs >= self.patience:
            print(f"Early stop at {state.stage_epoch_log} epoch")
            state.need_early_stop = True