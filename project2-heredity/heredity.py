import csv
import itertools
import sys

PROBS = {

    # Unconditional probabilities for having gene
    "gene": {
        2: 0.01,
        1: 0.03,
        0: 0.96
    },

    "trait": {

        # Probability of trait given two copies of gene
        2: {
            True: 0.65,
            False: 0.35
        },

        # Probability of trait given one copy of gene
        1: {
            True: 0.56,
            False: 0.44
        },

        # Probability of trait given no gene
        0: {
            True: 0.01,
            False: 0.99
        }
    },

    # Mutation probability
    "mutation": 0.01
}


def main():

    # Check for proper usage
    if len(sys.argv) != 2:
        sys.exit("Usage: python heredity.py data.csv")
    people = load_data(sys.argv[1])

    # Keep track of gene and trait probabilities for each person
    probabilities = {
        person: {
            "gene": {
                2: 0,
                1: 0,
                0: 0
            },
            "trait": {
                True: 0,
                False: 0
            }
        }
        for person in people
    }

    # Loop over all sets of people who might have the trait
    names = set(people)
    for have_trait in powerset(names):

        # Check if current set of people violates known information
        fails_evidence = any(
            (people[person]["trait"] is not None and
             people[person]["trait"] != (person in have_trait))
            for person in names
        )
        if fails_evidence:
            continue

        # Loop over all sets of people who might have the gene
        for one_gene in powerset(names):
            for two_genes in powerset(names - one_gene):

                # Update probabilities with new joint probability
                p = joint_probability(people, one_gene, two_genes, have_trait)
                update(probabilities, one_gene, two_genes, have_trait, p)

    # Ensure probabilities sum to 1
    normalize(probabilities)

    # Print results
    for person in people:
        print(f"{person}:")
        for field in probabilities[person]:
            print(f"  {field.capitalize()}:")
            for value in probabilities[person][field]:
                p = probabilities[person][field][value]
                print(f"    {value}: {p:.4f}")


def load_data(filename):
    """
    Load gene and trait data from a file into a dictionary.
    File assumed to be a CSV containing fields name, mother, father, trait.
    mother, father must both be blank, or both be valid names in the CSV.
    trait should be 0 or 1 if trait is known, blank otherwise.
    """
    data = dict()
    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"]
            data[name] = {
                "name": name,
                "mother": row["mother"] or None,
                "father": row["father"] or None,
                "trait": (True if row["trait"] == "1" else
                          False if row["trait"] == "0" else None)
            }
    return data


def powerset(s):
    """
    Return a list of all possible subsets of set s.
    """
    s = list(s)
    return [
        set(s) for s in itertools.chain.from_iterable(
            itertools.combinations(s, r) for r in range(len(s) + 1)
        )
    ]


def _genotype(one_gene, two_genes, name):
    if name in one_gene:
        gene = 1
    elif name in two_genes:
        gene = 2
    else:
        gene = 0
    return gene


def _genotype_prob(people, one_gene, two_genes, name):
    """
    Return the conditional probability
    that the given name has this genotype.
    """
    genotype = _genotype(one_gene, two_genes, name)

    father = people[name]["father"]
    mother = people[name]["mother"]

    if father is None:
        prob = PROBS["gene"][genotype]
    else:
        genetic_from_father = _pass_gene_probability(one_gene, two_genes, father)
        genetic_from_mother = _pass_gene_probability(one_gene, two_genes, mother)

        if genotype == 0:
            prob = (1 - genetic_from_father) * (1 - genetic_from_mother)
        elif genotype == 1:
            prob = (
                genetic_from_father * (1 - genetic_from_mother)
                + (1 - genetic_from_father) * genetic_from_mother
            )
        else:
            prob = genetic_from_father * genetic_from_mother

    return prob


def _pass_gene_probability(one_gene, two_genes, name):
    """
    Return the probability that the given name
    passes a disease-causing gene to his children.
    """
    genotype = _genotype(one_gene, two_genes, name)

    if genotype == 0:
        return PROBS["mutation"]
    elif genotype == 1:
        return 0.5
    else:
        return (1 - PROBS["mutation"])


def _genotype_joint_prob(people, one_gene, two_genes):
    joint_prob = 1

    for name in people:
        joint_prob *= _genotype_prob(people, one_gene, two_genes, name)

    return joint_prob


def _trait_joint_prob_when_genotype(people, one_gene, two_genes, have_trait):
    trait_joint_prob = 1
    for name in people:
        gene = _genotype(one_gene, two_genes, name)
        trait_joint_prob *= PROBS["trait"][gene][name in have_trait]
    return trait_joint_prob


def joint_probability(people, one_gene, two_genes, have_trait):
    """
    Compute and return a joint probability.

    The probability returned should be the probability that
        * everyone in set `one_gene` has one copy of the gene, and
        * everyone in set `two_genes` has two copies of the gene, and
        * everyone not in `one_gene` or `two_gene` does not have the gene, and
        * everyone in set `have_trait` has the trait, and
        * everyone not in set` have_trait` does not have the trait.
    """
    return (
        _genotype_joint_prob(people, one_gene, two_genes)
        * _trait_joint_prob_when_genotype(people, one_gene, two_genes, have_trait)
    )


def update(probabilities, one_gene, two_genes, have_trait, p):
    """
    Add to `probabilities` a new joint probability `p`.
    Each person should have their "gene" and "trait" distributions updated.
    Which value for each distribution is updated depends on whether
    the person is in `have_gene` and `have_trait`, respectively.
    """
    for person in probabilities:
        genotype = _genotype(one_gene, two_genes, person)
        probabilities[person]["gene"][genotype] += p
        probabilities[person]["trait"][person in have_trait] += p


def _normalize_dict(source_dict: dict):
    normalization_factor = sum(source_dict.values())
    for key in source_dict:
        source_dict[key] /= normalization_factor


def normalize(probabilities):
    """
    Update `probabilities` such that each probability distribution
    is normalized (i.e., sums to 1, with relative proportions the same).
    """
    for person in probabilities:
        _normalize_dict(probabilities[person]["gene"])
        _normalize_dict(probabilities[person]["trait"])


if __name__ == "__main__":
    main()
