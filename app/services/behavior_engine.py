"""
Advanced Behavioral Intelligence Layer.
Enhances honeypot realism through intent tracking, timing simulation, and human behavior modeling.
"""

import asyncio
import random
import re
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import deque


@dataclass
class BehaviorMetrics:
    """Container for behavioral analysis metrics."""
    confidence: float = 0.0
    escalation_rate: int = 0
    aggression_slope: float = 0.0
    delay_applied: float = 0.0
    reply_length_class: str = "medium"


class IntentTracker:
    """
    Track scammer maliciousness probability across conversation.
    Uses exponential smoothing for rolling risk estimate.
    """
    
    ALPHA = 0.3  # Smoothing factor (current weight)
    
    def __init__(self):
        self._confidence: float = 0.0
        self._turn_count: int = 0
        
    def update(self, scam_score: float, signal_count: int, 
               has_otp: bool, has_upi: bool, has_threat: bool, has_urgency: bool) -> float:
        """
        Update intent confidence based on current turn signals.
        
        Args:
            scam_score: Detector's risk score (0-10)
            signal_count: Number of triggered signals
            has_otp: OTP request detected
            has_upi: UPI request detected
            has_threat: Threat detected
            has_urgency: Urgency words detected
            
        Returns:
            Updated confidence [0, 1]
        """
        # Normalize current score to [0, 1]
        normalized = scam_score / 10.0
        
        # Boost for high-risk indicators
        if has_otp:
            normalized = min(1.0, normalized + 0.2)
        if has_threat:
            normalized = min(1.0, normalized + 0.15)
        if has_upi:
            normalized = min(1.0, normalized + 0.1)
        if has_urgency:
            normalized = min(1.0, normalized + 0.05)
            
        # Signal density boost
        normalized = min(1.0, normalized + signal_count * 0.02)
        
        # Exponential smoothing
        if self._turn_count == 0:
            self._confidence = normalized
        else:
            self._confidence = (1 - self.ALPHA) * self._confidence + self.ALPHA * normalized
        
        self._turn_count += 1
        
        return self._confidence
    
    @property
    def confidence(self) -> float:
        return round(self._confidence, 3)
    
    def reset(self):
        self._confidence = 0.0
        self._turn_count = 0


class EscalationAnalyzer:
    """
    Measure how fast scammer escalates requests.
    Tracks progression through severity levels.
    """
    
    # Severity levels
    LEVEL_GREETING = 0
    LEVEL_INFO = 1
    LEVEL_SENSITIVE = 2  # UPI, Account
    LEVEL_CRITICAL = 3   # OTP, Money
    LEVEL_THREAT = 4     # Police, Legal
    
    def __init__(self):
        self._previous_level: int = 0
        self._current_level: int = 0
        self._history: List[int] = []
        
    def analyze(self, message: str) -> int:
        """
        Analyze message and compute escalation rate.
        
        Returns:
            Escalation rate (level change from previous turn)
        """
        msg = message.lower()
        
        # Determine current level
        level = self.LEVEL_GREETING
        
        if any(w in msg for w in ["police", "arrest", "legal", "court", "jail", "case"]):
            level = self.LEVEL_THREAT
        elif any(w in msg for w in ["otp", "code", "pin", "password", "money", "transfer", "pay"]):
            level = self.LEVEL_CRITICAL
        elif any(w in msg for w in ["upi", "account", "bank", "number", "ifsc", "@"]):
            level = self.LEVEL_SENSITIVE
        elif any(w in msg for w in ["name", "address", "verify", "check", "confirm"]):
            level = self.LEVEL_INFO
        
        # Calculate rate
        rate = level - self._previous_level
        
        # Update state
        self._previous_level = self._current_level
        self._current_level = level
        self._history.append(level)
        
        return rate
    
    @property
    def escalation_rate(self) -> int:
        return self._current_level - self._previous_level
    
    def reset(self):
        self._previous_level = 0
        self._current_level = 0
        self._history.clear()


class AggressionAnalyzer:
    """
    Measure tone aggression growth over conversation.
    Tracks urgency, threats, caps, repeated demands.
    """
    
    WINDOW_SIZE = 5  # Keep last N turns for slope calculation
    
    def __init__(self):
        self._scores: deque = deque(maxlen=self.WINDOW_SIZE)
        
    def analyze(self, message: str) -> float:
        """
        Analyze aggression indicators in message.
        
        Returns:
            Current aggression score
        """
        score = 0.0
        msg_lower = message.lower()
        
        # Urgency words
        urgency = ["urgent", "immediately", "now", "fast", "quick", "hurry", "asap"]
        score += sum(1 for w in urgency if w in msg_lower)
        
        # Threat words
        threats = ["block", "suspend", "arrest", "police", "legal", "freeze", "close"]
        score += sum(2 for w in threats if w in msg_lower)
        
        # ALL CAPS detection (significant caps ratio)
        caps_ratio = sum(1 for c in message if c.isupper()) / max(len(message), 1)
        if caps_ratio > 0.4:
            score += 1
            
        # Exclamation marks
        score += message.count("!") * 0.5
        
        # Repeated words (demands)
        words = msg_lower.split()
        if len(words) > 2:
            repeated = len(words) - len(set(words))
            score += min(repeated, 2) * 0.5
        
        self._scores.append(score)
        
        return score
    
    @property
    def aggression_slope(self) -> float:
        """Calculate linear slope of aggression over recent turns."""
        if len(self._scores) < 2:
            return 0.0
            
        # Simple linear regression slope
        n = len(self._scores)
        x_mean = (n - 1) / 2
        y_mean = sum(self._scores) / n
        
        numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(self._scores))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
            
        return round(numerator / denominator, 3)
    
    def reset(self):
        self._scores.clear()


class Humanizer:
    """
    Simulate human typing behavior with realistic delays and imperfections.
    All operations are async-safe and non-blocking.
    """
    
    # Typing simulation parameters
    BASE_LATENCY_MIN = 0.8
    BASE_LATENCY_MAX = 2.0
    CHAR_DELAY_MIN = 0.05
    CHAR_DELAY_MAX = 0.09
    
    # Typo settings
    TYPO_PROBABILITY = 0.03  # 3% chance per applicable word
    TYPO_MAP = {
        "please": "plese",
        "account": "acount", 
        "verify": "verfiy",
        "transfer": "tranfer",
        "payment": "payemnt",
        "immediately": "immediatly",
        "receive": "recieve",
        "message": "mesage",
        "number": "numbr",
        "problem": "problm",
    }
    
    # Reply length classes
    LENGTH_SHORT = (4, 8)
    LENGTH_MEDIUM = (8, 15)
    LENGTH_LONG = (15, 25)
    
    def __init__(self):
        self._last_delay: float = 0.0
        
    def choose_reply_length(self) -> Tuple[str, Tuple[int, int]]:
        """Randomly choose reply length class."""
        r = random.random()
        if r < 0.25:
            return "short", self.LENGTH_SHORT
        elif r < 0.75:
            return "medium", self.LENGTH_MEDIUM
        else:
            return "long", self.LENGTH_LONG
            
    def apply_typos(self, text: str) -> str:
        """
        Apply subtle, occasional typos.
        Max 1 typo per ~25-30 words.
        """
        words = text.split()
        word_count = len(words)
        
        # Skip if too short
        if word_count < 8:
            return text
            
        # Limit typos based on length
        max_typos = max(1, word_count // 25)
        typos_applied = 0
        
        result = []
        for word in words:
            word_lower = word.lower().strip(".,!?")
            
            # Check if word is in typo map and probability hits
            if (word_lower in self.TYPO_MAP and 
                typos_applied < max_typos and 
                random.random() < self.TYPO_PROBABILITY):
                
                # Preserve original case pattern
                replacement = self.TYPO_MAP[word_lower]
                if word[0].isupper():
                    replacement = replacement.capitalize()
                    
                # Preserve punctuation
                if word[-1] in ".,!?":
                    replacement += word[-1]
                    
                result.append(replacement)
                typos_applied += 1
            else:
                result.append(word)
                
        return " ".join(result)
    
    def calculate_delay(self, response: str) -> float:
        """
        Calculate realistic typing delay for response.
        
        Args:
            response: The response text
            
        Returns:
            Delay in seconds
        """
        # Base thinking time
        base = random.uniform(self.BASE_LATENCY_MIN, self.BASE_LATENCY_MAX)
        
        # Typing time (with slight randomization per character)
        char_delay = random.uniform(self.CHAR_DELAY_MIN, self.CHAR_DELAY_MAX)
        typing_time = len(response) * char_delay
        
        # Add small random variation
        variation = random.uniform(-0.2, 0.3)
        
        delay = base + typing_time + variation
        
        # Clamp to reasonable range (don't want too long delays)
        delay = max(0.5, min(delay, 5.0))
        
        self._last_delay = round(delay, 2)
        return delay
    
    async def apply_delay(self, response: str) -> None:
        """
        Apply realistic typing delay (async, non-blocking).
        
        Args:
            response: The response text
        """
        delay = self.calculate_delay(response)
        await asyncio.sleep(delay)
        
    @property
    def last_delay(self) -> float:
        return self._last_delay


class BehaviorEngine:
    """
    Main wrapper class for all behavioral intelligence features.
    Provides unified interface for agent integration.
    """
    
    def __init__(self):
        self.intent_tracker = IntentTracker()
        self.escalation_analyzer = EscalationAnalyzer()
        self.aggression_analyzer = AggressionAnalyzer()
        self.humanizer = Humanizer()
        
        self._metrics = BehaviorMetrics()
        
    async def process_reply(
        self,
        reply: str,
        scammer_msg: str,
        scam_score: float = 0.0,
        signal_count: int = 0,
        apply_delay: bool = True
    ) -> str:
        """
        Process reply through all behavior enhancements.
        
        Args:
            reply: Agent's composed reply
            scammer_msg: Scammer's message (for analysis)
            scam_score: Detector's risk score
            signal_count: Number of triggered signals
            apply_delay: Whether to apply typing delay
            
        Returns:
            Enhanced reply text
        """
        msg_lower = scammer_msg.lower()
        
        # Analyze scammer behavior
        has_otp = "otp" in msg_lower or "code" in msg_lower or "pin" in msg_lower
        has_upi = "upi" in msg_lower or "@" in msg_lower
        has_threat = any(w in msg_lower for w in ["police", "arrest", "block", "suspend"])
        has_urgency = any(w in msg_lower for w in ["urgent", "immediately", "now", "fast"])
        
        # Update trackers
        self.intent_tracker.update(
            scam_score, signal_count, has_otp, has_upi, has_threat, has_urgency
        )
        self.escalation_analyzer.analyze(scammer_msg)
        self.aggression_analyzer.analyze(scammer_msg)
        
        # Get reply length preference
        length_class, _ = self.humanizer.choose_reply_length()
        
        # Apply subtle typos
        enhanced_reply = self.humanizer.apply_typos(reply)
        
        # Apply human delay (async)
        if apply_delay:
            await self.humanizer.apply_delay(enhanced_reply)
        else:
            # Just calculate for metrics
            self.humanizer.calculate_delay(enhanced_reply)
        
        # Update metrics
        self._metrics = BehaviorMetrics(
            confidence=self.intent_tracker.confidence,
            escalation_rate=self.escalation_analyzer.escalation_rate,
            aggression_slope=self.aggression_analyzer.aggression_slope,
            delay_applied=self.humanizer.last_delay,
            reply_length_class=length_class
        )
        
        return enhanced_reply
    
    def get_metrics(self) -> Dict:
        """
        Get current behavioral metrics for logging.
        
        Returns:
            Dict with confidence, escalation_rate, aggression_slope, delay_applied
        """
        return {
            "confidence": self._metrics.confidence,
            "escalation_rate": self._metrics.escalation_rate,
            "aggression_slope": self._metrics.aggression_slope,
            "delay_applied": self._metrics.delay_applied,
            "reply_length_class": self._metrics.reply_length_class,
        }
    
    def reset(self):
        """Reset all trackers for new session."""
        self.intent_tracker.reset()
        self.escalation_analyzer.reset()
        self.aggression_analyzer.reset()


# Singleton instance for shared state across session
_engines: Dict[str, BehaviorEngine] = {}

def get_behavior_engine(session_id: str) -> BehaviorEngine:
    """Get or create behavior engine for session."""
    if session_id not in _engines:
        _engines[session_id] = BehaviorEngine()
    return _engines[session_id]

def cleanup_engine(session_id: str):
    """Remove engine when session ends."""
    if session_id in _engines:
        del _engines[session_id]
