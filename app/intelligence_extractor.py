"""
Intelligence Extraction Module.
Extracts actionable information from scam conversations.
"""

import re
from typing import List, Dict, Set
from app.models import ExtractedIntelligenceInternal, ConversationMessage, Message


class IntelligenceExtractor:
    """
    Extracts scam-related intelligence from conversations.
    Identifies bank accounts, UPI IDs, phone numbers, links, and keywords.
    """
    
    # Regex patterns for intelligence extraction
    PATTERNS = {
        # Bank account patterns (Indian format)
        "bank_accounts": [
            r"\b\d{9,18}\b",  # 9-18 digit account numbers
            r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{0,6}\b",  # Formatted account numbers
        ],
        
        # UPI ID patterns
        "upi_ids": [
            r"[a-zA-Z0-9._-]+@[a-zA-Z0-9]+",  # standard@vpa format
            r"[a-zA-Z0-9._-]+@ybl\b",  # PhonePe
            r"[a-zA-Z0-9._-]+@paytm\b",  # Paytm
            r"[a-zA-Z0-9._-]+@okicici\b",  # Google Pay ICICI
            r"[a-zA-Z0-9._-]+@oksbi\b",  # Google Pay SBI
            r"[a-zA-Z0-9._-]+@okaxis\b",  # Google Pay Axis
            r"[a-zA-Z0-9._-]+@okhdfcbank\b",  # Google Pay HDFC
            r"[a-zA-Z0-9._-]+@upi\b",  # Generic UPI
            r"[a-zA-Z0-9._-]+@apl\b",  # Amazon Pay
            r"[a-zA-Z0-9._-]+@ibl\b",  # ICICI
            r"[a-zA-Z0-9._-]+@sbi\b",  # SBI
        ],
        
        # Phone number patterns (Indian format)
        "phone_numbers": [
            r"\+91[\s-]?\d{10}",  # +91 format
            r"\b91\d{10}\b",  # 91 prefix
            r"\b[6-9]\d{9}\b",  # Indian mobile (starts with 6-9)
            r"\+\d{1,3}[\s-]?\d{10,12}",  # International format
        ],
        
        # URL/Link patterns
        "phishing_links": [
            r"https?://[^\s<>\"']+",
            r"www\.[^\s<>\"']+",
            r"bit\.ly/[a-zA-Z0-9]+",
            r"tinyurl\.com/[a-zA-Z0-9]+",
            r"[a-zA-Z0-9-]+\.(xyz|tk|ml|ga|cf|top|click|link|online|site|website)[^\s]*",
        ],
        
        # Email patterns
        "email_addresses": [
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        ],
    }
    
    # Suspicious keywords to track
    SUSPICIOUS_KEYWORDS = [
        # Urgency
        "urgent", "immediately", "today", "now", "asap", "hurry",
        "deadline", "expire", "last chance", "final warning",
        
        # Threats
        "blocked", "suspended", "frozen", "deactivated", "terminated",
        "legal action", "police", "arrest", "court", "lawsuit",
        
        # Financial
        "otp", "pin", "cvv", "password", "verify", "kyc",
        "transfer", "refund", "cashback",
        
        # Prize scams
        "won", "winner", "lottery", "prize", "reward", "congratulations",
        
        # Impersonation
        "rbi", "income tax", "government", "bank manager", "customer care",
    ]
    
    # Whitelist patterns (to avoid false positives)
    WHITELIST_DOMAINS = [
        r"google\.com", r"microsoft\.com", r"apple\.com",
        r"facebook\.com", r"twitter\.com", r"linkedin\.com",
        r"amazon\.in", r"flipkart\.com", r"paytm\.com",
        r"sbi\.co\.in", r"hdfcbank\.com", r"icicibank\.com",
    ]
    
    def __init__(self):
        """Initialize the intelligence extractor."""
        self.compiled_patterns = {
            key: [re.compile(p, re.IGNORECASE) for p in patterns]
            for key, patterns in self.PATTERNS.items()
        }
        self.whitelist_compiled = [
            re.compile(p, re.IGNORECASE) for p in self.WHITELIST_DOMAINS
        ]
    
    def _is_whitelisted_url(self, url: str) -> bool:
        """Check if URL is from a whitelisted domain."""
        for pattern in self.whitelist_compiled:
            if pattern.search(url):
                return True
        return False
    
    def _extract_pattern_matches(
        self, 
        text: str, 
        patterns: List[re.Pattern]
    ) -> Set[str]:
        """Extract all matches for given patterns."""
        matches = set()
        for pattern in patterns:
            found = pattern.findall(text)
            matches.update(found)
        return matches
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and standardize phone number format."""
        # Remove spaces and dashes
        cleaned = re.sub(r"[\s-]", "", phone)
        
        # Ensure +91 prefix for Indian numbers
        if len(cleaned) == 10 and cleaned[0] in "6789":
            cleaned = "+91" + cleaned
        elif len(cleaned) == 12 and cleaned.startswith("91"):
            cleaned = "+" + cleaned
        
        return cleaned
    
    def _extract_suspicious_keywords(self, text: str) -> List[str]:
        """Extract suspicious keywords from text."""
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in self.SUSPICIOUS_KEYWORDS:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def extract_from_message(self, text: str) -> ExtractedIntelligenceInternal:
        """Extract intelligence from a single message."""
        intelligence = ExtractedIntelligenceInternal()
        
        # Extract bank accounts
        bank_matches = self._extract_pattern_matches(
            text, self.compiled_patterns["bank_accounts"]
        )
        # Filter out likely non-account numbers (phone numbers, etc.)
        for match in bank_matches:
            cleaned = re.sub(r"[\s-]", "", match)
            # Account numbers are typically 9-18 digits
            if 9 <= len(cleaned) <= 18:
                # Avoid phone numbers
                if not (len(cleaned) == 10 and cleaned[0] in "6789"):
                    intelligence.bankAccounts.append(cleaned)
        
        # Extract UPI IDs
        upi_matches = self._extract_pattern_matches(
            text, self.compiled_patterns["upi_ids"]
        )
        intelligence.upiIds = list(set(upi_matches) - {"@"})
        
        # Extract phone numbers
        phone_matches = self._extract_pattern_matches(
            text, self.compiled_patterns["phone_numbers"]
        )
        intelligence.phoneNumbers = [
            self._clean_phone_number(p) for p in phone_matches
        ]
        
        # Extract and filter phishing links
        link_matches = self._extract_pattern_matches(
            text, self.compiled_patterns["phishing_links"]
        )
        for link in link_matches:
            if not self._is_whitelisted_url(link):
                intelligence.phishingLinks.append(link)
        
        # Extract email addresses
        email_matches = self._extract_pattern_matches(
            text, self.compiled_patterns["email_addresses"]
        )
        intelligence.emailAddresses = list(email_matches)
        
        # Extract suspicious keywords
        intelligence.suspiciousKeywords = self._extract_suspicious_keywords(text)
        
        return intelligence
    
    def extract_from_conversation(
        self, 
        current_message: Message,
        history: List[ConversationMessage]
    ) -> ExtractedIntelligenceInternal:
        """
        Extract intelligence from entire conversation.
        Combines intelligence from all messages.
        """
        combined = ExtractedIntelligenceInternal()
        
        # Process history
        for msg in history:
            msg_intel = self.extract_from_message(msg.text)
            self._merge_intelligence(combined, msg_intel)
        
        # Process current message
        current_intel = self.extract_from_message(current_message.text)
        self._merge_intelligence(combined, current_intel)
        
        # Deduplicate all lists
        combined.bankAccounts = list(set(combined.bankAccounts))
        combined.upiIds = list(set(combined.upiIds))
        combined.phoneNumbers = list(set(combined.phoneNumbers))
        combined.phishingLinks = list(set(combined.phishingLinks))
        combined.emailAddresses = list(set(combined.emailAddresses))
        combined.suspiciousKeywords = list(set(combined.suspiciousKeywords))
        
        return combined
    
    def _merge_intelligence(
        self, 
        target: ExtractedIntelligenceInternal, 
        source: ExtractedIntelligenceInternal
    ) -> None:
        """Merge source intelligence into target."""
        target.bankAccounts.extend(source.bankAccounts)
        target.upiIds.extend(source.upiIds)
        target.phoneNumbers.extend(source.phoneNumbers)
        target.phishingLinks.extend(source.phishingLinks)
        target.emailAddresses.extend(source.emailAddresses)
        target.suspiciousKeywords.extend(source.suspiciousKeywords)
    
    def get_intelligence_summary(self, intel: ExtractedIntelligenceInternal) -> str:
        """Generate a human-readable summary of extracted intelligence."""
        parts = []
        
        if intel.bankAccounts:
            parts.append(f"Bank accounts: {len(intel.bankAccounts)}")
        if intel.upiIds:
            parts.append(f"UPI IDs: {len(intel.upiIds)}")
        if intel.phoneNumbers:
            parts.append(f"Phone numbers: {len(intel.phoneNumbers)}")
        if intel.phishingLinks:
            parts.append(f"Suspicious links: {len(intel.phishingLinks)}")
        if intel.emailAddresses:
            parts.append(f"Email addresses: {len(intel.emailAddresses)}")
        
        if parts:
            return "Extracted: " + ", ".join(parts)
        return "No actionable intelligence extracted yet"
