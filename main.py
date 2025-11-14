import ollama

EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
LANGUAGE_MODEL = 'hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF'


VECTOR_DB = []

# Load and chunk dataset
with open('dataset.text', 'r') as f:
  content = f.read()
  dataset = [chunk.strip() for chunk in content.split('\n') if chunk.strip()]

def add_chunk_to_database(chunk):
  embedding = ollama.embed(model=EMBEDDING_MODEL, input=chunk)['embeddings'][0]
  VECTOR_DB.append((chunk, embedding))


multilineChunk = None
for chunk in dataset:
  if chunk.startswith("[i]"):
    multilineChunk = ""  # Start a new multiline chunk
    continue
  elif chunk.startswith("[/i]") and multilineChunk is not None:
    add_chunk_to_database(multilineChunk.strip())
    multilineChunk = None
    continue
  if multilineChunk is not None:
    multilineChunk += (chunk + "\n")
  else:
    add_chunk_to_database(chunk)


def cosine_similarity(a, b):
  dot_product = sum([x * y for x, y in zip(a, b)])
  norm_a = sum([x ** 2 for x in a]) ** 0.5
  norm_b = sum([x ** 2 for x in b]) ** 0.5
  return dot_product / (norm_a * norm_b)

def retrieve(query, top_n=3):
  query_embedding = ollama.embed(model=EMBEDDING_MODEL, input=query)['embeddings'][0]
  # temporary list to store (chunk, similarity) pairs
  similarities = []
  for chunk, embedding in VECTOR_DB:
    similarity = cosine_similarity(query_embedding, embedding)
    similarities.append((chunk, similarity))
  # sort by similarity in descending order, because higher similarity means more relevant chunks
  similarities.sort(key=lambda x: x[1], reverse=True)
  # finally, return the top N most relevant chunks
  return similarities[:top_n]


input_query = input('Ask me a question: ')
retrieved_knowledge = retrieve(input_query)

# print('Retrieved knowledge:')
# for chunk, similarity in retrieved_knowledge:
#   print(f' - (similarity: {similarity:.2f}) {chunk}')

instruction_prompt = f'''You are a helpful chatbot.
Use only the following pieces of context to answer the question. Don't make up any new information. Also transform the information into a concise and clear answer. Make sure answer is in markdown format.:
{'\n'.join([f' - {chunk}' for chunk, similarity in retrieved_knowledge])}
'''


# stream the response from the chatbot
stream = ollama.chat(
  model=LANGUAGE_MODEL,
  messages=[
    {'role': 'system', 'content': instruction_prompt},
    {'role': 'user', 'content': input_query},
  ],
  stream=True,
)

# print the response from the chatbot in real-time
print('Chatbot response:')

response_content = ""
for chunk in stream:
  response_content += chunk['message']['content']


print(response_content.strip())