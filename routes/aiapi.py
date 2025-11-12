import os
import re
import pandas as pd
from transformers import pipeline
import json
import torch
from transformers import BertTokenizer, BertModel, BertForQuestionAnswering, BertConfig,Trainer, TrainingArguments
import random
import openai
# from templates import template
from .templates import template
# from resources.templa
from fastapi import APIRouter, Body, HTTPException, Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import google.generativeai as genai
from numpy import random
import numpy as np

router = APIRouter()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

genai.configure(api_key="AIzaSyC4wPorehJw5_dOKR5DVFrEMOuKIb1_jD0")
from pydantic import BaseModel
class QueryRequest(BaseModel):
    query: str

@router.post('/productWithoutModel')
async def product_without_model(request: QueryRequest):

    # df = pd.read_csv("./data/fashion_products_csv.csv")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "data", "fashion_products_csv.csv")
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.lower()
    df['price'] = df['price'].astype(str)
    df["rating"] = round(df['rating'], 2)
    query = request.query
    # Parse the incoming JSON body
    # request_data = await request.json()
    # query = request_data.get('query')
    # query = "Show all black Dress of men"
    if not query:
        raise HTTPException(status_code=400, detail="No query provided")

    query_words = query.split()
    result = df.copy()

    # Define patterns for price and rating filters
    price_range_pattern = r'(\d+(\.\d+)?)\s*(?:to|and)\s*(\d+(\.\d+)?)\s*\w*'
    above_pattern = r'(?:above|more than|above than)\s*(\d+(\.\d+)?)\s*\w*'
    below_pattern = r'(?:below|less than|less|below than|under)\s*(\d+(\.\d+)?)\s*\w*'
    rating_pattern = r'rating(?:\s*is)?\s*(less than|greater than|between)?\s*(\d+(\.\d+)?)\s*(?:and)?\s*(\d+(\.\d+)?)?'

    # Price range filtering
    price_range_match = re.search(price_range_pattern, query)
    if price_range_match:
        range_start = float(price_range_match.group(1))
        range_end = float(price_range_match.group(3))
        result = result[result['price'].astype(float).between(range_start, range_end)]
        print(f"Filtering by price range: {range_start} to {range_end}")

    # Above price filtering
    above_match = re.search(above_pattern, query)
    if above_match:
        above_price = float(above_match.group(1))
        result = result[result['price'].astype(float) > above_price]
        print(f"Filtering by price above: {above_price}")

    # Below price filtering
    below_match = re.search(below_pattern, query)
    if below_match:
        below_price = float(below_match.group(1))
        result = result[result['price'].astype(float) < below_price]
        print(f"Filtering by price below: {below_price}")

    # Rating filtering
    rating_match = re.search(rating_pattern, query)
    if rating_match:
        comparison_type = rating_match.group(1)
        if comparison_type == 'less than':
            max_rating = float(rating_match.group(2))
            result = result[result['rating'] < max_rating]
        elif comparison_type == 'greater than':
            min_rating = float(rating_match.group(2))
            result = result[result['rating'] > min_rating]
        elif comparison_type == 'between':
            min_rating = float(rating_match.group(2))
            max_rating = float(rating_match.group(4))
            result = result[(result['rating'] >= min_rating) & (result['rating'] <= max_rating)]
        else:
            specific_rating = float(rating_match.group(2))
            result = result[result['rating'] == specific_rating]

    # Filtering based on query words in various columns
    for word in query_words:
        # Check if the word exists in category
        if any(result['category'].str.contains(r'\b{}\b'.format(word), case=False, regex=True)):
            print(f"Complete word '{word}' in the query is found in 'category' column.")
            result = result[result['category'].str.contains(r'\b{}\b'.format(word), case=False, regex=True)]
    
    for word in query_words:
        # Check if the word exists in product name
        if any(result['product name'].str.contains(r'\b{}\b'.format(word), case=False, regex=True)):
            print(f"Complete word '{word}' in the query is found in 'product name' column.")
            result = result[result['product name'].str.contains(r'\b{}\b'.format(word), case=False, regex=True)]

        # Check if the word exists in color
        if any(result['color'].str.contains(r'\b{}\b'.format(word), case=False, regex=True)):
            print(f"Complete word '{word}' in the query is found in 'color' column.")
            result = result[result['color'].str.contains(r'\b{}\b'.format(word), case=False, regex=True)]

        # Check if the word exists in size
        if any(result['size'].str.contains(r'\b{}\b'.format(word), case=False, regex=True)):
            result = result[result['size'].str.contains(r'\b{}\b'.format(word), case=False, regex=True)]

        # Check if the word exists in brand
        if any(result['brand'].str.contains(r'\b{}\b'.format(word), case=False, regex=True)):
            print(f"Filtering by brand: {word}")
            result = result[result['brand'].str.contains(r'\b{}\b'.format(word), case=False, regex=True)]

    # Return the filtered results as JSON
    return JSONResponse(content=result.to_dict(orient="records"))

# Example queries, one at a time
query1 = "Show all black Dress of men"
query2 = "Show all Adidas products"
query3 = "Show all products with price less than 50"
query4 = "Show all products with rating above 3"
query5 = "Show all products of size XL"
query6 = "Show all products with price range 40 to 80"
query7 = "Show all products with price above than 50"
query8 = "Show all black Dress of women under 50"
query9 = "show all black dress of women under 50 and their rating is under 4"
# Applying the queries
# print("i hgot===-==================",generate_response(query1))
# print("i hgot===-==================",generate_response(query2))
# print("i hgot===-==================",generate_response(query3))
# print("i hgot===-==================",generate_response(query4))
# print("i hgot===-==================",generate_response(query5))
# print("i hgot===-==================",generate_response(query6))
# print("i hgot===-==================",generate_response(query7))
# print("i hgot===-==================",generate_response(query8))

@router.post('/productWithTapasModel',)
async def product_with_tapas_model(request: QueryRequest):
    # Parse the incoming JSON request
    # request_data = await request.json()
    # query = request_data.get('query')
    query = request.query
    
    if not query:
        raise HTTPException(status_code=400, detail="No query provided")

    # Load the dataset
    # data = pd.read_csv('./data/fashion_data_test.csv')
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "data", "fashion_data_test.csv")
    data = pd.read_csv(file_path)
    data = data.astype(str)

    # Initialize the TAPAS model and tokenizer
    tapas = pipeline(model="google/tapas-large-finetuned-wtq", tokenizer="google/tapas-large-finetuned-wtq")

    try:
        # Use TAPAS to query the dataset and retrieve the coordinates of matching cells
        results = tapas(table=data, query=query)
        print("TAPAS raw result:", results)
        # Extract matching rows from the dataframe based on the coordinates
        # matching_rows = [data.iloc[i[0]] for i in results['coordinates']]
        coords = results.get("coordinates", [])
        matching_rows = []

        for (row_idx, _) in coords:
            matching_rows.append(data.iloc[row_idx])

        if not matching_rows:
            return JSONResponse(content={"message": "No matching results found"}, status_code=200)

        # Convert the matching rows to a DataFrame and then to JSON
        matching_rows_df = pd.DataFrame(matching_rows)
        matching_rows_json = matching_rows_df.to_json(orient='records')
        matching_rows_json_object = json.loads(matching_rows_json)

        # Log the result (optional)
        print(matching_rows_json_object)

        # Return the matching rows as JSON response
        return JSONResponse(content=matching_rows_json_object)
    
    except Exception as e:
        import traceback
        print("🔥 TAPAS ERROR:", traceback.format_exc())
        # Handle exceptions during the model inference
        raise HTTPException(status_code=500, detail=f"Error processing query with TAPAS: {str(e)}")
    
    # return matching_rows.to_json(orient='records')

def evaluate_expression(x, keyword, operator):
    if operator == '<':
        return keyword.lower() in x and x < keyword.lower()
    elif operator == '>':
        return keyword.lower() in x and x > keyword.lower()
    else:
        return keyword.lower() in x
    

    
@router.post('/productWithBertModel')
def productWithBertModel(request: QueryRequest):
    query = request.query
    if not query:
        raise HTTPException(status_code=400, detail="No query provided")

    operator = re.findall(r'([<>==])', query)
    operator = operator[0] if operator else None

    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "data", "fashion_products_csv.csv")
    data = pd.read_csv(file_path)

    nlp = pipeline("text-classification", model="nlptown/bert-base-multilingual-uncased-sentiment")

    keywords = query.split()
    columns = ['Brand', 'Product Name', 'Category', 'Color', 'Size', 'Category', "Price", "Rating"]

    data = data.applymap(lambda x: str(x).lower())

    matching_keywords = []
    for keyword in keywords:
        if data[columns].applymap(lambda x: keyword.lower() in x).any().any():
            matching_keywords.append(keyword)

    print("Matching Keywords:", matching_keywords)

    # Filter data based on the matching keywords and operator
    matching_rows = data
    for keyword in matching_keywords:
        if operator:
            matching_rows = matching_rows[matching_rows[columns].applymap(lambda x: evaluate_expression(x, keyword, operator)).any(axis=1)]
        else:
            matching_rows = matching_rows[matching_rows[columns].applymap(lambda x: keyword.lower() in x).any(axis=1)]

    # Apply BERT sentiment analysis on the filtered rows
    sentiments = []
    for index, row in matching_rows.iterrows():
        text = row['Product Name']  # You can choose a different column for sentiment analysis if needed
        sentiment = nlp(text)[0]
        sentiments.append(sentiment)

    matching_rows['Sentiment'] = sentiments

    matching_rows_df = pd.DataFrame(matching_rows)
    matching_rows_json = matching_rows_df.to_json(orient='records')  # Convert the list to a DataFrame

    matching_rows_json_object = json.loads(matching_rows_json)

    return matching_rows_json_object



@router.post('/productWithBertTokenModel')
def productWithBertTokenModel(request: QueryRequest):
    search_query = request.query
    if not search_query:
        raise HTTPException(status_code=400, detail="No query provided")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "data", "fashion_products_csv.csv")
    df = pd.read_csv(file_path)

    df['Price'] = df['Price'].astype(str)  # Ensure Price is string for tokenization
    df['Rating'] = df['Rating'].astype(str)  # Ensure Rating is string for tokenization
    
    # Combine relevant product columns into a single string per row
    text_data = df['Product Name'] + " " + df['Brand'] + " " + df['Category'] + " " + df['Color'] + " " + df['Size'] + " " + df['Price'] + " " + df['Rating']
    
    # Step 2: Initialize tokenizer and model from BERT
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertModel.from_pretrained('bert-base-uncased')

    # Tokenize the combined text data for all products
    inputs = tokenizer(text_data.tolist(), padding=True, truncation=True, return_tensors="pt")

    # Step 3: Get embeddings for all products
    with torch.no_grad():
        outputs = model(**inputs)
        product_embeddings = outputs.last_hidden_state.mean(dim=1)  # Mean pooling for sentence embeddings

    # Step 4: Tokenize the search query
    search_inputs = tokenizer(search_query, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        search_outputs = model(**search_inputs)
        search_embedding = search_outputs.last_hidden_state.mean(dim=1)  # Mean pooling for the search query

    # Step 5: Compute cosine similarity between the search embedding and product embeddings
    cosine_similarities = torch.nn.functional.cosine_similarity(search_embedding, product_embeddings)

    # Define a threshold for similarity
    threshold = 0.5  # You can adjust the threshold based on your needs
    similar_product_indices = cosine_similarities > threshold
    similar_product_indices = similar_product_indices.numpy()
    # Step 6: Filter products based on cosine similarity threshold
    similar_products = df.loc[similar_product_indices]

    # Convert the filtered products to JSON format
    matching_rows_json = similar_products.to_json(orient='records')
    matching_rows_json_object = json.loads(matching_rows_json)
    return matching_rows_json_object


@router.get('/getAnswerWithoutModel')
def getAnswerWithoutModel():
    questions = [
        "What is your date of birth?",
        "What is your current address?",
        "Are you married? If so, what is your spouse’s full name and date of birth?",
        "Do you have children? If so, what are their names and dates of birth?",
        "Do you have any other dependents or individuals you support financially?",
        "Who do you want to serve as the executor of your will?",
        "List all your assets, such as real estate, bank accounts, investments, and personal property.",
        "Specify how you want your assets distributed among beneficiaries.",
        "Clarify if you have specific bequests, such as sentimental items or charitable donations?",
        "Outline your preferences for your funeral or memorial service."
    ]

    # Generate a meaningful random name
    first_names = ["Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace", "Henry", "Isabella", "Jack", "Kate", "Liam", "Mia", "Noah", "Olivia", "Peter", "Quinn", "Rachel", "Samuel", "Tina", "Ursula", "Victor", "Wendy", "Xander", "Yvonne", "Zachary"]
    random_name = random.choice(first_names)

    def generate_random_name():
        return random.choice(first_names)

    def generate_random_date():
        return f"{random.randint(1, 28)}/{random.randint(1, 12)}/{random.randint(1950, 2020)}"

    def generate_marriage_children_answer():
        is_married = random.choice([True, False])
        if is_married:
            spouse_name = generate_random_name()
            spouse_dob = generate_random_date()
            return f"Yes, {spouse_name}, born on {spouse_dob}"
        else:
            return "No"

    marriage_answer = generate_marriage_children_answer()
    children_answer = generate_marriage_children_answer()

    def generate_random_answers():
        return [
            f"Random Date {random.randint(1, 28)}/{random.randint(1, 12)}/{random.randint(1950, 2020)}",
            f"{random.randint(100, 999)} Random Street, {random_name}, State",
            f"{marriage_answer}",
            f"{children_answer}",
            "None",
            f"{random_name}",
            "Real estate, bank accounts, investments",
            "Equally among all beneficiaries",
            "No specific bequests",
            "Simple funeral service"
        ]

    random_answers = generate_random_answers()

    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertForQuestionAnswering.from_pretrained('bert-large-uncased-whole-word-masking-finetuned-squad')

    bert_answers = []
    question_list = []
    random_answers_list = []
    bert_answers_list = []

    for question, answer in zip(questions, random_answers):
        context = answer

        inputs = tokenizer(question, context, return_tensors='pt', max_length=512, truncation=True)

        outputs = model(**inputs)
        answer_start_scores = outputs.start_logits
        answer_end_scores = outputs.end_logits

        answer_start = torch.argmax(answer_start_scores)
        answer_end = torch.argmax(answer_end_scores) + 1

        bert_answer = tokenizer.convert_tokens_to_string(tokenizer.convert_ids_to_tokens(inputs["input_ids"][0][answer_start:answer_end]))

        bert_answers.append(bert_answer)
        question_list.append(question)
        random_answers_list.append(answer)

    data = {'Question': question_list, 'Random_Answer': random_answers_list}
    df = pd.DataFrame(data)

    matching_rows_json = df.to_json(orient='records')
    matching_rows_json_object = json.loads(matching_rows_json)

    return matching_rows_json_object

def getAnswer(sample_question):
    # Step 1: Load and preprocess the dataset
    # train_data = pd.read_csv('./data/question_dataset.csv') 
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "data", "question_dataset.csv")
    train_data = pd.read_csv(file_path)

     # Adjust the file path accordingly
    # Step 2: Initialize the BERT tokenizer and model
    tokenizer = BertTokenizer.from_pretrained('bert-large-uncased')
    model = BertForQuestionAnswering.from_pretrained('bert-large-uncased')
    # model_save_path = "models/bert_model_trained.pth"
    # model = BertForQuestionAnswering.from_pretrained(model_save_path,local_files_only=True)
    # model.eval()


    # # Select a random context from the training dataset for the predefined question
    sample_contexts = train_data[train_data['question'] == sample_question]['context'].values
    sample_context = random.choice(sample_contexts)

    # Tokenize the sample question and context
    inputs = tokenizer(sample_context, return_tensors='pt', max_length=512, truncation=True)

    # Use the trained model to generate an answer
    outputs = model(**inputs)
    answer_start_scores = outputs.start_logits
    answer_end_scores = outputs.end_logits

    answer_start = torch.argmax(answer_start_scores)
    answer_end = torch.argmax(answer_end_scores) + 1

    bert_answer = tokenizer.convert_tokens_to_string(tokenizer.convert_ids_to_tokens(inputs["input_ids"][0][answer_start:answer_end]))

    # Return the result
    data = {'Question': [sample_question], 'BERT Answer': [bert_answer]}
    df = pd.DataFrame(data, index=[0])
    return df

@router.get('/getAnswerFromBertModel')
def getAnswerFromBertModel():
    
    sample_questions = [
        "What is your date of birth?",
        "What is your current address?",
        "Are you married? If so what is your spouse’s full name and date of birth?",
        "Do you have children? If so what are their names and dates of birth?",
        "Do you have any other dependents or individuals you support financially?",
        "Who do you want to serve as the executor of your will?",
        "List all your assets such as real estate bank accounts investments and personal property.",
        "Specify how you want your assets distributed among beneficiaries",
        "Clarify if you have specific bequests such as sentimental items or charitable donations?",
        "Outline your preferences for your funeral or memorial service"
    ]

    # Step 1: Load and preprocess the dataset
    # train_data = pd.read_csv('./data/question_dataset.csv')  
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "data", "question_dataset.csv")
    train_data = pd.read_csv(file_path)

    # Adjust the file path accordingly

    # Step 2: Initialize the BERT tokenizer and model
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertForQuestionAnswering.from_pretrained('bert-large-uncased-whole-word-masking-finetuned-squad')

    results = []
    # answers_in_paragraph = []
    for sample_question in sample_questions:
        sample_contexts = train_data[train_data['question'] == sample_question]['context'].values
        if len(sample_contexts) > 0:
            sample_context = random.choice(sample_contexts)
            inputs = tokenizer(sample_question, sample_context, return_tensors='pt', max_length=512, truncation=True)
            outputs = model(**inputs)
            answer_start_scores = outputs.start_logits
            answer_end_scores = outputs.end_logits
            answer_start = torch.argmax(answer_start_scores)
            answer_end = torch.argmax(answer_end_scores) + 1
            bert_answer = tokenizer.convert_tokens_to_string(tokenizer.convert_ids_to_tokens(inputs["input_ids"][0][answer_start:answer_end]))
            # answers_in_paragraph.append(sample_context)
            # paragraph = " ".join(answers_in_paragraph) 
            data = {'question': [sample_question],'answer': [bert_answer]}
            # print("------------",paragraph)
            # data = {'Question': [sample_question], 'Context': [sample_context], 'BERT Answer': [bert_answer]}
            df = pd.DataFrame(data, index=[0])
            results.append(df)

    final_result = pd.concat(results, ignore_index=True)
    matching_rows_json = final_result.to_json(orient='records')
    # print("===========",paragraph)
    #return matching_rows_json
    # Create a Python dictionary with the "status" and "data" keys and their values
    response_data = {
        "status": "success",  # You can set the status value as needed
        "data": json.loads(matching_rows_json)
    }

    print(response_data)
    return response_data

@router.get('/getBioDataAnswerFromBertModel')
def getBioDataAnswerFromBertModel():
    sample_questions = [
        "What state are you in?",
        "What is your full name?",
        "What is your date of birth?",
        "What is your current address?",
        "What is your social security number?",
        "Are you married?",
        "What is your spouse’s full name and date of birth?",
        "Do you have children?",
        "What are their dates of birth of your children?",
        "Who do you want to serve as the executor of your will?",
        "Do you have a secondary choice for executor?",
        "What are the major assets you own?",
        "Do you have bank accounts, retirement accounts, or other financial accounts?",
        "Do you own any businesses or have interests in partnerships or other entities?",
        "How do you want your assets to be distributed upon your death?",
        "Are there specific bequests you want to leave?",
        "If you have minor children, do you want to set up a trust for their benefit?",
        "If you have minor children, who do you want to serve as their guardian?",
        "Do you have a secondary choice for guardian?",
        "Do you have any outstanding debts?",
        "How do you want these debts to be handled?",
        "Do you have specific wishes for your funeral or memorial service?",
        "Do you have a preferred burial or cremation method?",
        "Have you made any pre-arrangements related to your funeral or burial?",
        "Do you have digital assets that need to be addressed in your will?",
        "How do you want these assets to be handled?",
        "Are there any charitable donations you want to make?",
        "Do you have any other specific wishes or instructions?"
    ]

    # Load dataset
    try:
        # train_data = pd.read_csv('./data/updated_question_answers.csv') 
        train_data = pd.read_csv("D:/fastapi-mongo-master/routes/data/updated_question_answers.csv")

         # Adjust the file path accordingly
    except FileNotFoundError:
        return json.dumps({"status": "error", "message": "Dataset not found"})

    # Initialize BERT model and tokenizer
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertForQuestionAnswering.from_pretrained('bert-large-uncased-whole-word-masking-finetuned-squad')

    results = []

    for sample_question in sample_questions:
        sample_contexts = train_data[train_data['question'] == sample_question]['context'].values

        if len(sample_contexts) > 0:
            sample_context = random.choice(sample_contexts)

            # Get BERT answer for the question
            bert_answer = get_bert_answer(sample_question, sample_context, tokenizer, model)

            # Skip unnecessary follow-up questions (based on special conditions)
            if sample_question == "Are you married?" and "i am not married" in bert_answer.lower():
                results.append({'question': sample_question, 'answer': bert_answer})
                continue  # Skip further questions about marriage
            if sample_question == "Do you have children?" and "i do not have children" in bert_answer.lower():
                results.append({'question': sample_question, 'answer': bert_answer})
                continue  # Skip further questions about children

            results.append({'question': sample_question, 'answer': bert_answer})
        else:
            results.append({'question': sample_question, 'answer': "No context found"})

    # Convert results to DataFrame and JSON
    final_result = pd.DataFrame(results)
    matching_rows_json = final_result.to_json(orient='records')

    # Prepare the response
    response_data = {
        "status": "success",
        "data": json.loads(matching_rows_json)
    }

    json_response = json.dumps(response_data)
    return json_response

def get_bert_answer(question, context, tokenizer, model):
    inputs = tokenizer(question, context, return_tensors='pt', max_length=512, truncation=True)
    outputs = model(**inputs)
    answer_start_scores = outputs.start_logits
    answer_end_scores = outputs.end_logits

    answer_start = torch.argmax(answer_start_scores)
    answer_end = torch.argmax(answer_end_scores) + 1

    return tokenizer.convert_tokens_to_string(tokenizer.convert_ids_to_tokens(inputs["input_ids"][0][answer_start:answer_end]))

@router.get('/customWillTemplateOfMarriedPerson')
def customWillTemplateOfMarriedPerson():
  
    data = [
        {"answer": "John Smith"},
        {"answer": "123 Main St."},
        {"answer": "Anytown"},
        {"answer": "CA"},
        {"answer": "USA"},
        {"answer": "12345"},
        {"answer": "555-555-5555"},
        {"answer": "January 1, 1970"},
        {"answer": "Software Developer"},
        {"answer": "Married"},
        {"answer": "2 children: Jane Smith (born January 1, 2000) and John Smith Jr. (born January 1, 2005)"},
        {"answer": "Jane Smith"},
        {"answer": "Car (approximate value: $10,000)"},
        {"answer": "John Smith Jr."},
        {"answer": "Boat (approximate value: $20,000)"},
        {"answer": "Jane Doe"},
        {"answer": "Sister-in-law"},
        {"answer": "Jane Smith"},
        {"answer": "I have pre-planned my funeral arrangements."},
        {"answer": "Cremated and ashes scattered"},
        {"answer": "I direct that my organs be donated to the organ donation program."},
        {"answer": "I own a website and social media accounts. I direct my Executor to transfer ownership of these digital assets to my children: Jane Smith and John Smith Jr."},
    ]

     # Combine the data into a user prompt
    user_prompt = (
        "You are a lawyer helping a client draft their last will and testament. "
        "Based on the following information, draft the will:\n\n"
    )
    for item in data:
        user_prompt += f"- {item['answer']}\n"
   
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(user_prompt) 
    # response = genai.GenerativeModel(
    # model="gemini-pro",
    # messages=[
    #     {"role": "system", "content": "You are a lawyer helping a client draft their last will and testament. Here is the template you want to fill out:\n" + template},
    #     {"role": "user", "content": f"{data}"}
    # ]
    # )

    response_answer = response.choices[0].message['content']

    return response_answer
    
@router.get('/customWillTemplateOfPerson')
def customWillTemplateOfPerson():
  

    # Set up your OpenAI API key
    openai.api_key = OPENAI_API_KEY

    # Define the data
    data = [
        {
         
            "answer": "new york"
        },
        {
            "answer": "michael smith"
        },
        {
            "answer": "november 5 1982"
        },
        {
            "answer": "123 maple avenue otherville usa"
        },
        {
            "answer": "234 - 56 - 7890"
        },
        {
            "answer": "i am not married"
        },
        {
            "answer": "lisa brown"
        },
        {
            "answer": "i do not have children"
        },
        {
            "answer": "william williams"
        },
        {
            "answer": "amy johnson my sister"
        },
        {
            "answer": "beachfront property and art collection and antiques"
        },
        {
            "answer": "multiple bank accounts and investments"
        },
        {
            "answer": "board member of a multinational corporation"
        },
        {
            "answer": "among my immediate family members"
        },
        {
            "answer": "i want her to inherit a specific painting that holds sentimental value to our family"
        },
        {
            "answer": "creating a trust for my children ' s well - being"
        },
        {
            "answer": "my sister"
        },
        {
            "answer": "my cousin"
        },
        {
            "answer": "i have"
        },
        {
            "answer": "allocating specific portions of my estate to cover my debts"
        },
        {
            "answer": "i want my funeral"
        },
        {
            "answer": "traditional"
        },
        {
            "answer": "i have a detailed plan in place for my funeral arrangements including pre - arranged services"
        },
        {
            "answer": "i own a significant online collection"
        },
        {
            "answer": "securely transferred to my designated beneficiaries"
        },
        {
            "answer": "my will includes instructions for donating a part of my estate to wildlife conservation and environmental protection organizations"
        },
        {
            "answer": "specific personal possessions"
        }
    ]


    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a lawyer helping a client draft their last will and testament. Here is the template you want to fill out:\n" + template},
        {"role": "user", "content": f"{data}"}
    ]
    )

    response_answer = response.choices[0].message['content']
    return response_answer

    
@router.get('/GPTWillTemplateOfPerson')
def GPTWillTemplateOfPerson():
    # Set up your OpenAI API key
    openai.api_key = OPENAI_API_KEY
    # Define the data
    data = [
        {
         
            "answer": "new york"
        },
        {
            "answer": "michael smith"
        },
        {
            "answer": "november 5 1982"
        },
        {
            "answer": "123 maple avenue otherville usa"
        },
        {
            "answer": "234 - 56 - 7890"
        },
        {
            "answer": "i am not married"
        },
        {
            "answer": "lisa brown"
        },
        {
            "answer": "i do not have children"
        },
        {
            "answer": "william williams"
        },
        {
            "answer": "amy johnson my sister"
        },
        {
            "answer": "beachfront property and art collection and antiques"
        },
        {
            "answer": "multiple bank accounts and investments"
        },
        {
            "answer": "board member of a multinational corporation"
        },
        {
            "answer": "among my immediate family members"
        },
        {
            "answer": "i want her to inherit a specific painting that holds sentimental value to our family"
        },
        {
            "answer": "creating a trust for my children ' s well - being"
        },
        {
            "answer": "my sister"
        },
        {
            "answer": "my cousin"
        },
        {
            "answer": "i have"
        },
        {
            "answer": "allocating specific portions of my estate to cover my debts"
        },
        {
            "answer": "i want my funeral"
        },
        {
            "answer": "traditional"
        },
        {
            "answer": "i have a detailed plan in place for my funeral arrangements including pre - arranged services"
        },
        {
            "answer": "i own a significant online collection"
        },
        {
            "answer": "securely transferred to my designated beneficiaries"
        },
        {
            "answer": "my will includes instructions for donating a part of my estate to wildlife conservation and environmental protection organizations"
        },
        {
            "answer": "specific personal possessions"
        }
    ]

    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a lawyer helping a client draft their last will and testament.we do not need witness. use my answers and do not give suggestions. Add today date at the end and add my name instead of [Your Name]"},
        {"role": "user", "content": f"{data}"}
    ]
    )
    print(response)
    response_answer = response.choices[0].message['content']
    return response_answer

 
@router.post('/willByChatGpt')
def willByChatGpt(request: QueryRequest):
    # Set up your OpenAI API key
    openai.api_key = OPENAI_API_KEY
    
    #GET QUERY PARAMS 
    request_data = request.get_json()
    data = request_data.get('answer_data')
    
    # response = openai.ChatCompletion.create(
    response = openai.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a lawyer helping a client draft their last will and testament.we do not need witness. use my answers and do not give suggestions. Add today date at the end and add my name instead of [Your Name]"},
        {"role": "user", "content": f"{data}"}
    ]
    )
    print(response)
    response_answer = response.choices[0].message['content']
    response_data = {
        "status": "success",  # You can set the status value as needed
        "data": response_answer
    }

    # Serialize the dictionary into a JSON string
    json_response = json.dumps(response_data)

    # Now you have a JSON response with "status" and "data" keys
    print(json_response)
    return json_response





# Replace with your Google Generative AI API key

@router.get('/customWillTemplateOfMarriedPerson1')
def customWillTemplateOfMarriedPerson1():
    api_key = OPENAI_API_KEY
    # Define the data
    data = [
        {"answer": "John Smith"},
        {"answer": "123 Main St."},
        {"answer": "Anytown"},
        {"answer": "CA"},
        {"answer": "USA"},
        {"answer": "12345"},
        {"answer": "555-555-5555"},
        {"answer": "January 1, 1970"},
        {"answer": "Software Developer"},
        {"answer": "Married"},
        {"answer": "2 children: Jane Smith (born January 1, 2000) and John Smith Jr. (born January 1, 2005)"},
        {"answer": "Jane Smith"},
        {"answer": "Car (approximate value: $10,000)"},
        {"answer": "John Smith Jr."},
        {"answer": "Boat (approximate value: $20,000)"},
        {"answer": "Jane Doe"},
        {"answer": "Sister-in-law"},
        {"answer": "Jane Smith"},
        {"answer": "I have pre-planned my funeral arrangements."},
        {"answer": "Cremated and ashes scattered"},
        {"answer": "I direct that my organs be donated to the organ donation program."},
        {"answer": "I own a website and social media accounts. I direct my Executor to transfer ownership of these digital assets to my children: Jane Smith and John Smith Jr."},
    ]

    # Create a Gemini model client
    model = google_generativeai.GenerativeAI(api_key=api_key)

    # Prepare the prompt
    prompt = "You are a lawyer helping a client draft their last will and testament. Here is the template you want to fill out:\n" + template + "\n\n" + f"{data}"

    # Generate the response
    response = model.generate_content(prompt=prompt)
    print(response.text)
    return response.text


@router.post("/generate-product-names")
async def generate_product_content(
    prompt: str = Body(..., embed=True),
    mode: str = Body("name", embed=True)  # "name" or "description"
):
    if mode == "name":
        system_prompt = (
            f"\n{prompt}\n"
            "Return the names as a numbered list."
        )
    elif mode == "description":
        system_prompt = (
            f"\n{prompt}\n"
            "Return the descriptions in a paragraph."
        )
    elif mode == "variant":
        system_prompt = (
            f"\n{prompt}\n"
            "Return the variant names as a numbered list."
        )
    else:
        return {"error": "Invalid mode. Use 'name' or 'description'."}

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for product content."},
            {"role": "user", "content": system_prompt}
        ],
        max_tokens=300,
        temperature=0.8,
    )
    text = response.choices[0].message.content
    items = [line.split('. ', 1)[-1] for line in text.strip().split('\n') if line.strip()]
    return {"results": items}