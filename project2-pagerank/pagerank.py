import os
import random
import re
import sys

DAMPING = 0.85
SAMPLES = 10000


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python pagerank.py corpus")
    corpus = crawl(sys.argv[1])
    ranks = sample_pagerank(corpus, DAMPING, SAMPLES)
    print(f"PageRank Results from Sampling (n = {SAMPLES})")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")
    ranks = iterate_pagerank(corpus, DAMPING)
    print(f"PageRank Results from Iteration")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")


def crawl(directory):
    """
    Parse a directory of HTML pages and check for links to other pages.
    Return a dictionary where each key is a page, and values are
    a list of all other pages in the corpus that are linked to by the page.
    """
    pages = dict()

    # Extract all links from HTML files
    for filename in os.listdir(directory):
        if not filename.endswith(".html"):
            continue
        with open(os.path.join(directory, filename)) as f:
            contents = f.read()
            links = re.findall(r"<a\s+(?:[^>]*?)href=\"([^\"]*)\"", contents)
            pages[filename] = set(links) - {filename}

    # Only include links to other pages in the corpus
    for filename in pages:
        pages[filename] = set(
            link for link in pages[filename]
            if link in pages
        )

    return pages


def transition_model(corpus, page, damping_factor):
    """
    Return a probability distribution over which page to visit next,
    given a current page.

    With probability `damping_factor`, choose a link at random
    linked to by `page`. With probability `1 - damping_factor`, choose
    a link at random chosen from all pages in the corpus.
    """
    # 如果没有链接到其他页面，则视为链接到了所有页面
    if len(corpus[page]) != 0:
        linked_pages = corpus[page]
    else:
        linked_pages = corpus.keys()

    total_pages = len(corpus)
    total_linked_pages = len(linked_pages)

    next_page_probability = dict()
    for next_page in corpus:
        if next_page in linked_pages:
            next_page_probability[next_page] = \
                (1 - damping_factor) / total_pages + damping_factor * 1.0 / total_linked_pages
        else:
            next_page_probability[next_page] = (1 - damping_factor) / total_pages

    return next_page_probability


def sample_pagerank(corpus, damping_factor, n):
    """
    Return PageRank values for each page by sampling `n` pages
    according to transition model, starting with a page at random.

    Return a dictionary where keys are page names, and values are
    their estimated PageRank value (a value between 0 and 1). All
    PageRank values should sum to 1.
    """
    pagerank = dict.fromkeys(corpus.keys(), 0)

    current_page = random.choice(list(corpus))
    pagerank[current_page] += 1.0 / n

    for i in range(n - 1):
        next_page_probability = transition_model(corpus, current_page, damping_factor)

        probability = random.random()
        cumulative_probability = 0
        for page in next_page_probability:
            cumulative_probability += next_page_probability[page]
            if cumulative_probability >= probability:
                current_page = page
                pagerank[current_page] += 1.0 / n
                break

    return pagerank


def _pagerank_iterate(corpus, pagerank, damping_factor):
    new_pagerank = dict.fromkeys(corpus.keys(), 0)
    total_pages = len(corpus)
    for page in corpus:
        new_pagerank[page] += (1 - damping_factor) / total_pages

        if len(corpus[page]) != 0:
            linked_pages = corpus[page]
        else:
            linked_pages = corpus.keys()

        total_linked_pages = len(linked_pages)
        for linked_page in linked_pages:
            new_pagerank[linked_page] += damping_factor * pagerank[page] / total_linked_pages

    return new_pagerank


def iterate_pagerank(corpus, damping_factor):
    """
    Return PageRank values for each page by iteratively updating
    PageRank values until convergence.

    Return a dictionary where keys are page names, and values are
    their estimated PageRank value (a value between 0 and 1). All
    PageRank values should sum to 1.
    """
    iteration_cutoff = 0.001

    pagerank = dict.fromkeys(corpus.keys(), 1.0 / len(corpus))

    iteration_continue = True
    while iteration_continue:
        new_pagerank = _pagerank_iterate(corpus, pagerank, damping_factor)
        iteration_continue = any(
            abs(new_pagerank[page] - pagerank[page]) > iteration_cutoff
            for page in corpus 
        )
        pagerank = new_pagerank

    return pagerank


if __name__ == "__main__":
    main()
