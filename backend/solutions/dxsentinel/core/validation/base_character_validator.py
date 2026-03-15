class BaseCharacterValidator:
    """
    Base para validadores de caracteres inválidos.
    Define los caracteres problemáticos y métodos de detección comunes.
    """

    # Caracteres completamente inválidos
    INVALID_CHARS = frozenset({
        '\ufffd',  # Replacement character (�) - indica encoding corrupto
        '\x00',  # NULL byte - no debería estar en CSVs
    })

    # Caracteres sospechosos (típicamente Windows-1252 mal interpretado)
    SUSPICIOUS_CHARS = frozenset({
        '\x80', '\x81', '\x82', '\x83', '\x84', '\x85', '\x86', '\x87',
        '\x88', '\x89', '\x8a', '\x8b', '\x8c', '\x8d', '\x8e', '\x8f',
        '\x90', '\x91', '\x92', '\x93', '\x94', '\x95', '\x96', '\x97',
        '\x98', '\x99', '\x9a', '\x9b', '\x9c', '\x9d', '\x9e', '\x9f',
    })

    @classmethod
    def detect_problematic_chars(cls, text: str) -> tuple[set, set]:
        invalid_chars = set()
        suspicious_chars = set()

        for char in text:
            if char in cls.INVALID_CHARS:
                invalid_chars.add(char)
            elif char in cls.SUSPICIOUS_CHARS:
                suspicious_chars.add(char)

        return invalid_chars, suspicious_chars

    @staticmethod
    def has_replacement_character(text: str) -> bool:
        return '\ufffd' in text

    @staticmethod
    def format_char_repr(chars: set) -> str:
        return ', '.join([repr(c) for c in sorted(chars)])
