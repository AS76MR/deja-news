

def important_named_entities (text) :
    try:
        ner_pipeline = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")
        print (text)
        entities_dicts = ner_pipeline(text)
        entities = []
        for d in entities_dicts:
            entities.append(d['word'])

        entities = list(set(entities))
        print (entities)

        client = openai.OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{
            "role": "user",
            "content": f"Assign 0-100 importance scores to: {entities} based on centrality to this text: {text}. Please give the output as a simple dict of enetity:score without any commenst or explanations"
        }]
    )
        print (response.choices[0].message.content)

        entity_score_dict = ast.literal_eval(response.choices[0].message.content)
        print (entity_score_dict)
        key_entities = [key for key, value in entity_score_dict.items() if value > 75]
        return key_entities
    except:
        return []



