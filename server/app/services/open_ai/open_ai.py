# ================= IMPORTS ==================
from openai import OpenAI
import re
import json
import unicodedata
from typing import Optional, List
import base64


from server.app.utils.formatters.localisation import localize_au
from server.config.ConfigHelper import ConfigHelper


# ================= CONSTANTS ==================

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

# ================= CLASS DEFINITION ==================
class OpenAIHelper:
    def __init__(self):
        # Use ConfigHelper instead of Firestore
        cfg = ConfigHelper.get_openai_client_config()
        self.client = OpenAI(**cfg)

    def generate_text(self, prompt, model="gpt-4o-mini", max_tokens=200):
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                # max_tokens=max_tokens
            )
            # Correct way to access the response
            generated_text = response.choices[0].message.content
            generated_text = self.strip_code_blocks(generated_text)  # Strip code block markers
            return self.localize_au(generated_text)
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return None
    
    def get_embedding(self, text_or_texts, model="text-embedding-3-small"):
        try:
            if isinstance(text_or_texts, str):
                texts = [text_or_texts]
            else:
                texts = text_or_texts

            response = self.client.embeddings.create(
                model=model,
                input=texts
            )
            embeddings = [d.embedding for d in response.data]
            return embeddings[0] if isinstance(text_or_texts, str) else embeddings
        except Exception as e:
            print(f"OpenAI Embedding API error: {e}")
            return None
        
    def generate_image(self, prompt: str, model: str = "dall-e-3", size: str = "1024x1024", ) -> Optional[dict]:
        """
        Generate an image from a prompt.

        Returns a dict:
        {
          "bytes": <raw_image_bytes>,      # for uploading via requests/files
          "b64": "<base64_string>",        # if you want to store/log
          "mime": "image/png"
        }
        or None on error.
        """
        try:
            # Build kwargs so we can conditionally add response_format
            kwargs = {
                "model": model,
                "prompt": prompt,
                "n": 1,
                "size": size,
            }

            # For dall-e-3 we *must* explicitly request b64_json
            if model == "dall-e-3":
                kwargs["response_format"] = "b64_json"

            response = self.client.images.generate(**kwargs)

            # The new client uses attributes, not dicts
            first = response.data[0]
            b64_data = getattr(first, "b64_json", None)

            if not b64_data:
                print("[OpenAI] No b64_json field on image response.")
                return None

            img_bytes = base64.b64decode(b64_data)

            return {
                "bytes": img_bytes,
                "b64": b64_data,
                "mime": "image/png",
            }
        except Exception as e:
            print(f"OpenAI Image API error: {e}")
            return None

    
    # ========== HELPERS ==============
    def localize_au(self, text):
        return localize_au(text)
    
    def strip_code_blocks(self, text):
        # Remove code block markers (` ```html` and ` ``` `)
        text = re.sub(r'^```html\n', '', text)  # Strip starting code block
        text = re.sub(r'```$', '', text)  # Strip ending code block
        return text.strip()  # Remove any leading or trailing whitespace
    
    def normalize_whitespace(self, text):
        # Replace multiple spaces/newlines with a single space or newline
        text = re.sub(r'\s+', ' ', text)  # normalize all whitespace to single space
        return text.strip()
    
    def normalize_unicode(self, text):
        return unicodedata.normalize('NFKC', text)
    
    def smart_quotes(self, text):
        text = text.replace('"', '“').replace("'", "‘")
        return text
    
    # ================= PRODUCT FUNCTIONS ==================
    def new_product_title(self, item, p_type="productTitle"):
        formatted_prompt, model = self.format_prompt(item, p_type)
        return self.generate_text(prompt=formatted_prompt, model=model)

    