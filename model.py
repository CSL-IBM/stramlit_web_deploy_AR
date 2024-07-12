# model.py

from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.foundation_models.extensions.langchain import WatsonxLLM
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams

class LLM:
    def __init__(self):
        my_credentials = {
            "url"    : "https://us-south.ml.cloud.ibm.com",
            "apikey" : "hkEEsPjALuKUCakgA4IuR0SfTyVC9uT0qlQpA15Rcy8U" # <--- NOTE: replace "YOUR_WATSONX_API" with your actual API key) 
        }

        params = {
            GenParams.MAX_NEW_TOKENS: 1000, # The maximum number of tokens that the model can generate in a single run.
            GenParams.TEMPERATURE: 0.1,   # A parameter that controls the randomness of the token generation. A lower value makes the generation more deterministic, while a higher value introduces more randomness.
        }

        LLAMA2_model = Model(
            model_id= 'meta-llama/llama-2-70b-chat', 
            credentials=my_credentials,
            params=params,
            project_id="16acfdcc-378f-4268-a2f4-ba04ca7eca08",  # <--- NOTE: replace "YOUR_PROJECT_ID" with your actual project ID
        )

        self.llm = WatsonxLLM(LLAMA2_model)

# Instantiate the LLM object
llm_object = LLM()
llm = llm_object.llm
