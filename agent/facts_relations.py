"""Question patterns SADAH answers directly from Wikidata.

Each entry: (property id, regex capturing the subject, Arabic answer template, English answer template).
Templates receive {e} = subject name, {v} = value, {d} = extra detail (e.g. the population year).
Order matters: the first matching pattern wins. "P2048|P2044" means: try P2048, then P2044.
"""

# Properties that often have several true values (founders, languages): show up to three.
MULTI_VALUED = {"P112", "P37", "P30"}

RELATIONS = [
    ("P36", r"عاصمة\s+(.+)|capital(?: city)? of\s+(.+)", "عاصمة {e} هي **{v}**.", "The capital of {e} is **{v}**."),
    ("P1082", r"(?:عدد\s+)?سكان\s+(.+)|population of\s+(.+)|how many people live in\s+(.+)",
     "عدد سكان {e} حوالي **{v}** نسمة{d}.", "The population of {e} is about **{v}**{d}."),
    ("P571", r"(?:تأسست|تاسست|تأسس|تاسس|نشأت|قامت)\s+(.+)|when (?:was|were) (.+?) (?:founded|established|created)",
     "تأسست {e} في **{v}**.", "{e} was founded on **{v}**."),
    ("P38", r"عملة\s+(.+)|currency (?:of|in)\s+(.+)", "عملة {e} هي **{v}**.", "The currency of {e} is **{v}**."),
    ("P37", r"اللغة الرسمية (?:في|ل|لـ)\s*(.+)|official language (?:of|in)\s+(.+)",
     "اللغة الرسمية في {e} هي **{v}**.", "The official language of {e} is **{v}**."),
    ("P569", r"متى (?:ولد|ولدت|انولد)\s+(.+)|تاريخ ميلاد\s+(.+)|when (?:was|is) (.+?) born|birth ?date of\s+(.+)",
     "وُلد {e} في **{v}**.", "{e} was born on **{v}**."),
    ("P19", r"(?:اين|أين|وين) (?:ولد|ولدت|انولد)\s+(.+)|مكان ميلاد\s+(.+)|where (?:was|is) (.+?) born|birthplace of\s+(.+)",
     "وُلد {e} في **{v}**.", "{e} was born in **{v}**."),
    ("P2048|P2044", r"(?:كم )?(?:طول|ارتفاع)\s+(.+)|how tall is\s+(.+)|height of\s+(.+)|how high is\s+(.+)",
     "ارتفاع {e}: **{v}**.", "The height of {e} is **{v}**."),
    ("P2046", r"(?:كم )?مساحة\s+(.+)|area of\s+(.+)|how big is\s+(.+)", "مساحة {e}: **{v}**.", "The area of {e} is **{v}**."),
    ("P112", r"(?:من )?(?:مؤسس|اسس|أسس)\s+(.+)|who founded\s+(.+)|founder of\s+(.+)",
     "مؤسس {e}: **{v}**.", "{e} was founded by **{v}**."),
    # --- sports (SADAH v4)
    ("P286", r"(?:من )?(?:مدرب|يدرب)\s+(?:نادي\s+|فريق\s+)?(.+)|(?:who is the )?(?:head )?coach of\s+(.+)|who coaches\s+(.+)",
     "مدرب {e}: **{v}**.", "The head coach of {e} is **{v}**."),
    ("P115", r"(?:ملعب|استاد)\s+(?:نادي\s+|فريق\s+)?(.+)|(?:home )?stadium of\s+(.+)|where does (.+?) play home games",
     "ملعب {e}: **{v}**.", "The home stadium of {e} is **{v}**."),
    ("P118", r"(?:في )?(?:اي|أي|وش) دوري (?:يلعب )?(?:فيه )?(.+)|what league (?:is|does) (.+?) (?:in|play in)",
     "{e} يلعب في **{v}**.", "{e} plays in **{v}**."),
    ("P54", r"(?:في )?(?:اي|أي|وش) (?:نادي|فريق) (?:يلعب )?(?:فيه |له )?(.+)|(?:what|which) (?:team|club) does (.+?) play for",
     "{e} يلعب حالياً مع **{v}**.", "{e} currently plays for **{v}**."),
    ("P413", r"(?:وش|ما|ايش) مركز\s+(.+)|what position does (.+?) play",
     "مركز {e}: **{v}**.", "{e} plays as **{v}**."),
    ("P35", r"(?:من )?(?:رئيس|ملك|حاكم)\s+(?:دولة\s+)?(.+)|(?:who is the )?(?:president|king|head of state) of\s+(.+)",
     "رأس الدولة في {e}: **{v}**.", "The head of state of {e} is **{v}**."),
    ("P30", r"(?:في )?(?:اي|أي|وش) قارة (?:تقع )?(.+)|which continent is (.+?) in|continent of\s+(.+)",
     "{e} تقع في قارة **{v}**.", "{e} is in **{v}**."),
]

# Wikidata unit item -> (Arabic, English) symbol for quantities such as height and area
UNITS = {"Q11573": ("م", "m"), "Q828224": ("كم", "km"), "Q174728": ("سم", "cm"), "Q712226": ("كم²", "km²"),
         "Q25343": ("م²", "m²"), "Q35852": ("هكتار", "ha"), "Q3710": ("قدم", "ft")}
