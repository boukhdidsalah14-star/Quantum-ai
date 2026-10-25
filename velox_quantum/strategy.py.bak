from collections import deque
from dataclasses import dataclass

@dataclass
class Signal:
    direction: str
    reason: str
    confidence: float

class MomentumStrategy:
    """
    Educational example only: short rolling momentum.
    It is not validated, does not predict the future reliably, and can lose money.
    """
    def __init__(self, window: int = 8, threshold: float = 0.0):
        self.prices = deque(maxlen=max(3, window))
        self.threshold = threshold

    def update(self, price: float) -> Signal | None:
        self.prices.append(float(price))
        if len(self.prices) < self.prices.maxlen:
            return None
        change = self.prices[-1] - self.prices[0]
        if change > self.threshold:
            return Signal("CALL", f"rolling momentum +{change:g}", 0.5)
        if change < -self.threshold:
            return Signal("PUT", f"rolling momentum {change:g}", 0.5)
        return None
