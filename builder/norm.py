"""Letter normalisation shared by the rules: hamza/alef variants, ى/ي and ة/ه are typed interchangeably.
It maps character to character, so an index in the normalised text is the same index in the original."""
_ALEF = str.maketrans("أإآىة", "اااYه".replace("Y", "ي"))


def n(s: str) -> str:
    return s.translate(_ALEF)
