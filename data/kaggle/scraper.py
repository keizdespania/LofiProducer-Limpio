import wikipediaapi
import os
import csv
import re
from textblob import TextBlob
import textstat
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# ── Wikipedia setup ──────────────────────────────────────────
wiki = wikipediaapi.Wikipedia(
    language='en',
    extract_format=wikipediaapi.ExtractFormat.WIKI,
    user_agent='CognitiveBiasesProject/1.0'
)

# ── Create all folders ───────────────────────────────────────
folders = [
    'data/cognitive_biases',
    'data/logical_fallacies',
    'data/combined',
    'output'
]
for folder in folders:
    os.makedirs(folder, exist_ok=True)

# ── Topic Lists ──────────────────────────────────────────────

COGNITIVE_BIASES = [
    'Confirmation bias',
    'Dunning–Kruger effect',
    'Anchoring (cognitive bias)',
    'Availability heuristic',
    'Bandwagon effect',
    'Barnum effect',
    'Blind spot bias',
    'Choice-supportive bias',
    'Clustering illusion',
    'Curse of knowledge',
    'Decoy effect',
    'Framing effect (psychology)',
    'Fundamental attribution error',
    'Halo effect',
    'Hindsight bias',
    'Illusory superiority',
    'In-group favoritism',
    'Just-world hypothesis',
    'Negativity bias',
    'Optimism bias',
    'Ostrich effect',
    'Outcome bias',
    'Overconfidence effect',
    'Placebo effect',
    'Planning fallacy',
    'Recency bias',
    'Self-serving bias',
    'Status quo bias',
    'Stereotyping',
    'Sunk cost'
]

LOGICAL_FALLACIES = [
    'Ad hominem',
    'Appeal to authority',
    'Appeal to emotion',
    'Appeal to nature',
    'Argument from ignorance',
    'Bandwagon fallacy',
    'Begging the question',
    'Black swan theory',
    'Cherry picking (fallacy)',
    'Circular reasoning',
    'False analogy',
    'False dilemma',
    'Gambler\'s fallacy',
    'Hasty generalization',
    'Misleading vividness',
    'Nirvana fallacy',
    'Post hoc ergo propter hoc',
    'Red herring',
    'Slippery slope',
    'Straw man'
]

# ── Quick check ──────────────────────────────────────────────
print(f"Cognitive Biases to scrape: {len(COGNITIVE_BIASES)}")
print(f"Logical Fallacies to scrape: {len(LOGICAL_FALLACIES)}")
print(f"Total topics: {len(COGNITIVE_BIASES) + len(LOGICAL_FALLACIES)}")
def scrape_and_save(topic_name, category, folder_path):
    """
    Scrapes one Wikipedia topic and saves it as a .txt file.
    
    topic_name  — the Wikipedia page title (e.g. 'Confirmation bias')
    category    — 'Cognitive Bias' or 'Logical Fallacy'
    folder_path — where to save the .txt file
    """
    
    # Fetch the page from Wikipedia
    page = wiki.page(topic_name)
    
    # Check if page exists — not every title is perfect
    if not page.exists():
        print(f"  SKIPPED — Page not found: {topic_name}")
        return None
    
    # Clean the topic name to use as filename
    # e.g. 'Confirmation bias' → 'confirmation_bias'
    filename = topic_name.lower().replace(' ', '_').replace('/', '_')
    filename = filename.replace('(', '').replace(')', '').replace('–', '_')
    filepath = os.path.join(folder_path, filename + '.txt')
    
    # Build the content we will save in the file
    content = f"""TOPIC: {page.title}
CATEGORY: {category}
URL: https://en.wikipedia.org/wiki/{page.title.replace(' ', '_')}
{'='*60}
SUMMARY:
{page.summary}
{'='*60}
FULL TEXT:
{page.text}
"""
    
    # Write the content to the .txt file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  SAVED — {filename}.txt")
    
    # Return data we will need later for the CSV
    return {
        'category': category,
        'name': page.title,
        'summary': page.summary,
        'full_text': page.text,
    }


# ── TEST with just ONE topic ─────────────────────────────────
# ── Scrape ALL topics ────────────────────────────────────────
all_data = []  # this will collect data from all 50 topics

# ── Scrape Cognitive Biases ──────────────────────────────────
print("Scraping Cognitive Biases...")
print("-" * 40)

for topic in COGNITIVE_BIASES:
    result = scrape_and_save(
        topic,
        'Cognitive Bias',
        'data/cognitive_biases'
    )
    if result:                  # only add if page was found
        all_data.append(result)

# ── Scrape Logical Fallacies ─────────────────────────────────
print("\nScraping Logical Fallacies...")
print("-" * 40)

for topic in LOGICAL_FALLACIES:
    result = scrape_and_save(
        topic,
        'Logical Fallacy',
        'data/logical_fallacies'
    )
    if result:
        all_data.append(result)

# ── Summary ──────────────────────────────────────────────────
print("\n" + "=" * 40)
print(f"Scraping complete!")
print(f"Total topics successfully scraped: {len(all_data)}")

if all_data:
    print(f"\nPreview of what was returned:")
    print(f"Name: {all_data[0]['name']}")
    print(f"Summary (first 200 chars): {all_data[0]['summary'][:200]}")
    # ── Create Combined Master File ──────────────────────────────
print("\nCreating combined master file...")

combined_filepath = 'data/combined/all_topics.txt'

with open(combined_filepath, 'w', encoding='utf-8') as f:
    
    # Write a header for the file
    f.write("COGNITIVE BIASES & LOGICAL FALLACIES — WIKIPEDIA DATASET\n")
    f.write("Total Topics: " + str(len(all_data)) + "\n")
    f.write("="*60 + "\n\n")
    
    # Loop through every topic and write it into the master file
    for i, entry in enumerate(all_data, 1):
        f.write(f"ENTRY {i}\n")
        f.write(f"Category : {entry['category']}\n")
        f.write(f"Name     : {entry['name']}\n")
        f.write(f"{'-'*60}\n")
        f.write(f"Summary:\n{entry['summary']}\n\n")
        f.write(f"Full Text:\n{entry['full_text']}\n")
        f.write(f"{'='*60}\n\n")

print(f"  SAVED — all_topics.txt")
print(f"  Location: {combined_filepath}")
# ── Step 1: Compute TF-IDF keywords for all documents ────────────
print("\nComputing TF-IDF keywords...")

# Collect all full texts for TF-IDF computation
all_texts = [entry['full_text'] for entry in all_data]
all_names = [entry['name'] for entry in all_data]

# Build TF-IDF matrix across all 50 documents
vectorizer = TfidfVectorizer(
    max_features=5000,      # consider top 5000 words
    stop_words='english',   # remove common words like 'the', 'is'
    ngram_range=(1, 1)      # single words only
)

tfidf_matrix = vectorizer.fit_transform(all_texts)
feature_names = vectorizer.get_feature_names_out()

# For each document, extract its top 5 keywords
def get_top_keywords(tfidf_row, feature_names, top_n=5):
    # Get scores for this document
    scores = tfidf_row.toarray()[0]
    # Get indices of top scoring words
    top_indices = np.argsort(scores)[::-1][:top_n]
    # Return the actual words
    keywords = [feature_names[i] for i in top_indices if scores[i] > 0]
    return ', '.join(keywords)

print("  TF-IDF complete!")

# ── Step 2: Build the Rich CSV ───────────────────────────────────
print("\nBuilding enriched CSV dataset...")

csv_filepath = 'output/cognitive_biases_fallacies_dataset.csv'

fieldnames = [
    'category',
    'name',
    'summary',
    'full_text',
    'word_count',
    'char_count',
    'sentence_count',
    'avg_word_length',
    'sentiment_score',
    'sentiment_label',
    'reading_level',
    'top_keywords'
]

with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:

    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for i, entry in enumerate(all_data):

        text = entry['full_text']

        # ── Basic text features ──────────────────────────────
        words = text.split()
        word_count = len(words)
        char_count = len(text.replace(' ', ''))
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if s.strip()]
        sentence_count = len(sentences)
        avg_word_length = round(
            sum(len(w) for w in words) / word_count, 2
        ) if word_count > 0 else 0

        # ── Sentiment score (TextBlob) ────────────────────────
        blob = TextBlob(text)
        sentiment_score = round(blob.sentiment.polarity, 4)

        # Classify sentiment into a label
        if sentiment_score > 0.05:
            sentiment_label = 'Positive'
        elif sentiment_score < -0.05:
            sentiment_label = 'Negative'
        else:
            sentiment_label = 'Neutral'

        # ── Reading level (Flesch-Kincaid) ────────────────────
        reading_level = round(textstat.flesch_reading_ease(text), 2)

        # ── Top keywords (TF-IDF) ─────────────────────────────
        tfidf_row = tfidf_matrix[i]
        top_keywords = get_top_keywords(tfidf_row, feature_names)

        # ── Write row ─────────────────────────────────────────
        writer.writerow({
            'category'        : entry['category'],
            'name'            : entry['name'],
            'summary'         : entry['summary'],
            'full_text'       : entry['full_text'],
            'word_count'      : word_count,
            'char_count'      : char_count,
            'sentence_count'  : sentence_count,
            'avg_word_length' : avg_word_length,
            'sentiment_score' : sentiment_score,
            'sentiment_label' : sentiment_label,
            'reading_level'   : reading_level,
            'top_keywords'    : top_keywords
        })

        print(f"  Processed: {entry['name']}")

print(f"\n  SAVED — cognitive_biases_fallacies_dataset.csv")
print(f"  Location: {csv_filepath}")
print(f"  Rows written: {len(all_data)}")
print(f"  Columns: {len(fieldnames)}")