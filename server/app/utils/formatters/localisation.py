# ================= IMPORTS ==================
import re

# ================= CONSTANTS ==================


# ================= FUNCTIONS ==================
def capitalize_words(text):
    if not text is None: 
        return ' '.join(word.capitalize() for word in text.split())
    return None

def localize_au(text):
        
    AU_SPELLING = {
        'color': 'colour', 'optimize': 'optimise', 'behavior': 'behaviour', 'humor': 'humour',
        'realize': 'realise', 'prioritize': 'prioritise', 'analyze': 'analyse', 'organize': 'organise',
        'theater': 'theatre', 'meter': 'metre', 'center': 'centre', 'fulfill': 'fulfil',
        'enroll': 'enrol', 'installment': 'instalment', 'traveled': 'travelled', 'traveling': 'travelling',
        'labeled': 'labelled', 'labeling': 'labelling', 'modeled': 'modelled', 'modeling': 'modelling',
        'revolutionized': 'revolutionised', 'customized': 'customised', 'favor': 'favour',
        'honor': 'honour', 'jewelry': 'jewellery', 'defense': 'defence', 'license': 'licence',
        'maximize': 'maximise', 'specialized': 'specialised', 'stabilize': 'stabilise',
        'organization': 'organisation', "catalog": "catalogue", "gray": "grey", "favorite": "favourite",
        'organizing': 'organising', 'colouring': 'colouring', 'colourful': 'colourful', 'optimization': 'optimisation', 
        'behaviors': 'behaviours', 'humorists': 'humourists', 'realization': 'realisation', 'organizing': 'organising',
        'prioritization': 'prioritisation', 'analysis': 'analyses', 'organisation': 'organisation',
        'theatergoer': 'theatregoer', 'theaters': 'theatres', 'metre': 'metre', 'centers': 'centres',
        'fulfilling': 'fulfilling', 'fulfilment': 'fulfilment', 'enrolled': 'enrolled', 'installments': 'instalments',
        'traveled': 'travelled', 'traveller': 'traveller', 'labeled': 'labelled', 'labelling': 'labelling',
        'modeled': 'modelled', 'modeling': 'modelling', 'revolutionized': 'revolutionised', 'customized': 'customised',
        'favoring': 'favouring', 'honorary': 'honourary', 'jewelers': 'jewellers', 'defensive': 'defensive',
        'licenses': 'licences', 'maximize': 'maximise', 'specializations': 'specialisations', 'stabilized': 'stabilised',
        'organizational': 'organisational', 'cataloging': 'cataloguing', 'grayish': 'greyish', 'favorable': 'favourable',
    }

    for us_spelling, au_spelling in AU_SPELLING.items():
        # Use regex for case-insensitive replacements while maintaining original casing
        text = re.sub(rf'\b{us_spelling}\b', au_spelling, text, flags=re.IGNORECASE)
    return text