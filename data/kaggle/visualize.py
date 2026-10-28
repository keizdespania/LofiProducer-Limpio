import csv
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from collections import Counter

# ── Load the CSV ─────────────────────────────────────────────────
print("Loading dataset...")

data = []
with open('output/cognitive_biases_fallacies_dataset.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append(row)

print(f"  Loaded {len(data)} entries\n")

# Separate into two groups
biases    = [d for d in data if d['category'] == 'Cognitive Bias']
fallacies = [d for d in data if d['category'] == 'Logical Fallacy']

# ── INSIGHT 1: Average word count by category ────────────────────
bias_words     = [int(d['word_count']) for d in biases]
fallacy_words  = [int(d['word_count']) for d in fallacies]
avg_bias_words    = round(sum(bias_words) / len(bias_words))
avg_fallacy_words = round(sum(fallacy_words) / len(fallacy_words))

print("=" * 55)
print("INSIGHT 1 — Article Length")
print("=" * 55)
print(f"  Avg words per Cognitive Bias article   : {avg_bias_words}")
print(f"  Avg words per Logical Fallacy article  : {avg_fallacy_words}")
if avg_bias_words > avg_fallacy_words:
    diff = avg_bias_words - avg_fallacy_words
    print(f"  → Cognitive Biases are {diff} words longer on average")
else:
    diff = avg_fallacy_words - avg_bias_words
    print(f"  → Logical Fallacies are {diff} words longer on average")

# ── INSIGHT 2: Sentiment by category ────────────────────────────
bias_sentiment    = [float(d['sentiment_score']) for d in biases]
fallacy_sentiment = [float(d['sentiment_score']) for d in fallacies]
avg_bias_sent     = round(sum(bias_sentiment) / len(bias_sentiment), 4)
avg_fallacy_sent  = round(sum(fallacy_sentiment) / len(fallacy_sentiment), 4)

print("\n" + "=" * 55)
print("INSIGHT 2 — Sentiment Score")
print("=" * 55)
print(f"  Avg sentiment — Cognitive Biases  : {avg_bias_sent}")
print(f"  Avg sentiment — Logical Fallacies : {avg_fallacy_sent}")
print(f"  → Both categories have slightly positive Wikipedia tone")

# Sentiment label distribution
all_labels = [d['sentiment_label'] for d in data]
label_counts = Counter(all_labels)
print(f"\n  Sentiment breakdown across all 50 topics:")
for label, count in label_counts.items():
    print(f"    {label}: {count} articles")

# ── INSIGHT 3: Reading level ──────────────────────────────────────
bias_reading    = [float(d['reading_level']) for d in biases]
fallacy_reading = [float(d['reading_level']) for d in fallacies]
avg_bias_read   = round(sum(bias_reading) / len(bias_reading), 2)
avg_fallacy_read = round(sum(fallacy_reading) / len(fallacy_reading), 2)

print("\n" + "=" * 55)
print("INSIGHT 3 — Reading Level (Flesch-Kincaid)")
print("=" * 55)
print(f"  Score guide: 0-30 = Very Hard, 30-50 = Hard,")
print(f"               50-70 = Medium, 70-100 = Easy")
print(f"  Avg reading level — Cognitive Biases  : {avg_bias_read}")
print(f"  Avg reading level — Logical Fallacies : {avg_fallacy_read}")

# ── INSIGHT 4: Top 5 longest and shortest articles ───────────────
sorted_by_words = sorted(data, key=lambda x: int(x['word_count']), reverse=True)

print("\n" + "=" * 55)
print("INSIGHT 4 — Longest & Shortest Articles")
print("=" * 55)
print("  Top 5 longest:")
for d in sorted_by_words[:5]:
    print(f"    {d['name']:<40} {d['word_count']} words")
print("\n  Top 5 shortest:")
for d in sorted_by_words[-5:]:
    print(f"    {d['name']:<40} {d['word_count']} words")

# ── INSIGHT 5: Most positive and negative articles ───────────────
sorted_by_sent = sorted(data, key=lambda x: float(x['sentiment_score']), reverse=True)

print("\n" + "=" * 55)
print("INSIGHT 5 — Most Positive & Negative Articles")
print("=" * 55)
print("  Most positive tone:")
for d in sorted_by_sent[:3]:
    print(f"    {d['name']:<40} score: {d['sentiment_score']}")
print("\n  Most negative tone:")
for d in sorted_by_sent[-3:]:
    print(f"    {d['name']:<40} score: {d['sentiment_score']}")

# ════════════════════════════════════════════════════════════════
# VISUALIZATIONS
# ════════════════════════════════════════════════════════════════

print("\n\nGenerating charts...")
plt.style.use('seaborn-v0_8-darkgrid')
BIAS_COLOR    = '#4C72B0'
FALLACY_COLOR = '#DD8452'

# ── CHART 1: Word count by category (bar chart) ──────────────────
fig, ax = plt.subplots(figsize=(14, 7))

names  = [d['name'] for d in data]
words  = [int(d['word_count']) for d in data]
cats   = [d['category'] for d in data]
colors = [BIAS_COLOR if c == 'Cognitive Bias' else FALLACY_COLOR for c in cats]

bars = ax.bar(range(len(names)), words, color=colors, edgecolor='white', linewidth=0.5)

ax.set_xticks(range(len(names)))
ax.set_xticklabels(names, rotation=90, fontsize=7)
ax.set_ylabel('Word Count', fontsize=12)
ax.set_title('Word Count per Article — Cognitive Biases vs Logical Fallacies',
             fontsize=14, fontweight='bold', pad=20)

# Add average lines
ax.axhline(avg_bias_words,    color=BIAS_COLOR,    linestyle='--',
           linewidth=1.5, label=f'Avg Bias ({avg_bias_words} words)')
ax.axhline(avg_fallacy_words, color=FALLACY_COLOR, linestyle='--',
           linewidth=1.5, label=f'Avg Fallacy ({avg_fallacy_words} words)')

bias_patch    = mpatches.Patch(color=BIAS_COLOR,    label='Cognitive Bias')
fallacy_patch = mpatches.Patch(color=FALLACY_COLOR, label='Logical Fallacy')
ax.legend(handles=[bias_patch, fallacy_patch], fontsize=10)

plt.tight_layout()
plt.savefig('output/chart1_word_count.png', dpi=150, bbox_inches='tight')
plt.close()
print("  SAVED — chart1_word_count.png")

# ── CHART 2: Sentiment score by category (scatter) ───────────────
fig, ax = plt.subplots(figsize=(14, 6))

for i, d in enumerate(data):
    color = BIAS_COLOR if d['category'] == 'Cognitive Bias' else FALLACY_COLOR
    ax.scatter(i, float(d['sentiment_score']), color=color, s=80,
               zorder=3, edgecolors='white', linewidth=0.5)
    ax.text(i, float(d['sentiment_score']) + 0.005,
            d['name'][:12], fontsize=5, ha='center', rotation=90, alpha=0.7)

ax.axhline(0, color='gray', linestyle='-', linewidth=0.8, alpha=0.5)
ax.axhline(avg_bias_sent,    color=BIAS_COLOR,    linestyle='--',
           linewidth=1.5, label=f'Avg Bias Sentiment ({avg_bias_sent})')
ax.axhline(avg_fallacy_sent, color=FALLACY_COLOR, linestyle='--',
           linewidth=1.5, label=f'Avg Fallacy Sentiment ({avg_fallacy_sent})')

ax.set_ylabel('Sentiment Score (−1 Negative → +1 Positive)', fontsize=11)
ax.set_title('Sentiment Score per Article — Cognitive Biases vs Logical Fallacies',
             fontsize=14, fontweight='bold', pad=20)
ax.set_xticks([])
ax.legend(fontsize=10)

bias_patch    = mpatches.Patch(color=BIAS_COLOR,    label='Cognitive Bias')
fallacy_patch = mpatches.Patch(color=FALLACY_COLOR, label='Logical Fallacy')
ax.legend(handles=[bias_patch, fallacy_patch], fontsize=10)

plt.tight_layout()
plt.savefig('output/chart2_sentiment.png', dpi=150, bbox_inches='tight')
plt.close()
print("  SAVED — chart2_sentiment.png")

# ── CHART 3: Reading level distribution (histogram) ──────────────
fig, ax = plt.subplots(figsize=(10, 6))

ax.hist(bias_reading,    bins=10, alpha=0.7, color=BIAS_COLOR,
        label='Cognitive Bias',   edgecolor='white')
ax.hist(fallacy_reading, bins=10, alpha=0.7, color=FALLACY_COLOR,
        label='Logical Fallacy',  edgecolor='white')

ax.axvline(avg_bias_read,    color=BIAS_COLOR,    linestyle='--',
           linewidth=2, label=f'Avg Bias ({avg_bias_read})')
ax.axvline(avg_fallacy_read, color=FALLACY_COLOR, linestyle='--',
           linewidth=2, label=f'Avg Fallacy ({avg_fallacy_read})')

ax.set_xlabel('Flesch-Kincaid Reading Ease Score', fontsize=12)
ax.set_ylabel('Number of Articles', fontsize=12)
ax.set_title('Reading Level Distribution — Cognitive Biases vs Logical Fallacies',
             fontsize=14, fontweight='bold', pad=20)
ax.legend(fontsize=10)

# Add difficulty labels
ax.axvspan(0,  30, alpha=0.05, color='red')
ax.axvspan(30, 50, alpha=0.05, color='orange')
ax.axvspan(50, 70, alpha=0.05, color='yellow')
ax.axvspan(70, 100, alpha=0.05, color='green')

ax.text(15, ax.get_ylim()[1]*0.9, 'Very Hard', fontsize=8, color='red',   alpha=0.7)
ax.text(35, ax.get_ylim()[1]*0.9, 'Hard',      fontsize=8, color='orange', alpha=0.7)
ax.text(55, ax.get_ylim()[1]*0.9, 'Medium',    fontsize=8, color='olive',  alpha=0.7)
ax.text(75, ax.get_ylim()[1]*0.9, 'Easy',      fontsize=8, color='green',  alpha=0.7)

plt.tight_layout()
plt.savefig('output/chart3_reading_level.png', dpi=150, bbox_inches='tight')
plt.close()
print("  SAVED — chart3_reading_level.png")

print("\n✅ All charts saved to output/ folder")
print("✅ Copy the INSIGHTS above into your README!")