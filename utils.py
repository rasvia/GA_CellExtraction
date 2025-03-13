import random
import string


def create_individual(text, size_bounds, bits=3):
    if len(text) > 0:
        size_bounds[1] = min(size_bounds[1], len(text))
        word_size = random.randint(size_bounds[0], size_bounds[1]) * bits
        starting_pt = random.sample(range(0, len(text) - word_size, bits), k=1)[0]
        individual = text[starting_pt:starting_pt + word_size]
    else:
        individual = []
    return individual


def generate_population(population_size, text, size_bounds, cells):
    population = []
    while len(population) < population_size - len(cells):
        individual = create_individual(text, size_bounds)
        # if individual not in population and '\t' not in individual:
        if individual not in population:
            population.append(individual)
    population += cells
    return population


def count_frequency(population, text):
    frequencies = []
    for individual in population:
        frequencies.append(text.count(individual))
    return frequencies


def remove_substrings(strings):
    strings.sort(key=len, reverse=True)
    unique_strings = []

    for i, string in enumerate(strings):
        if not any(string in other for other in strings[:i]):
            unique_strings.append(string)
    return unique_strings


def selection(population, frequencies):
    wordPool = []
    dictionary = dict(zip(population, frequencies))
    for frequency in sorted(list(set(frequencies)), reverse=True):
        potential_words = [k for k, v in dictionary.items() if v == frequency]
        words = remove_substrings(potential_words)
        wordPool += words
    return wordPool


def filter_by_freq(population, frequencies):
    filtered = list(filter(lambda x: x[1] > 1, zip(population, frequencies)))
    filtered_pop = [word[0] for word in filtered]
    filtered_frequency = [word[1] for word in filtered]
    return filtered_pop, filtered_frequency


def fitness(text, population, frequency):
    sorted_population = sorted(zip(population, frequency), key=lambda x: (x[1], len(x[0])), reverse=True)
    temp_text = text
    for individual in sorted_population:
        sub_string = individual[0]
        temp_text = temp_text.replace(sub_string, '\t')
    temp_text = temp_text.replace('\t', '')
    score = 1 - len(temp_text) / len(text.replace('\t', ''))
    return score, temp_text


def find_overlap_and_merge(str1, str2, bits=3):
    def get_overlap(s1, s2):
        max_overlap = ''
        for i in range(0, min(len(s1), len(s2)), bits):
            if s1[-i:] == s2[:i]:
                max_overlap = s1[-i:]
        return max_overlap

    overlap1 = get_overlap(str1, str2)
    overlap2 = get_overlap(str2, str1)
    if len(overlap1) > len(overlap2):
        merged_string = str1 + str2[len(overlap1):]
        return overlap1, merged_string
    else:
        merged_string = str2 + str1[len(overlap2):]
        return overlap2, merged_string


def shorten_sequence(string, extend_length, bits=3):
    str_shortened = string[bits * random.randint(1, extend_length):-1 * bits * random.randint(1, extend_length)]
    str_shortened_right = string[:-1 * bits * random.randint(1, extend_length)]
    str_shortened_left = string[bits * random.randint(1, extend_length):]
    return [str_shortened, str_shortened_right, str_shortened_left]


def extend_sequence(string, extend_length, text, bits=3):
    try:
        res = [i for i in range(len(text)) if text.startswith(string, i)]
        starting_pt = random.sample(res, 1)[0]
        ending_pt = starting_pt + len(string)

        str_extended = text[starting_pt - bits * random.randint(1, extend_length):ending_pt + bits * random.randint(1,
                                                                                                                    extend_length)]
        str_extended_left = text[starting_pt - bits * random.randint(1, extend_length):ending_pt]
        str_extended_right = text[starting_pt:ending_pt + bits * random.randint(1, extend_length)]

        return [str_extended, str_extended_left, str_extended_right]
    except:
        return ['', '', '']


def mutation(str1, str2, size_bounds, text, bits=3):
    mutated_sequence = [str1, str2]
    extend_length = 10
    overlap, merged_string = find_overlap_and_merge(str1, str2)
    if len(overlap) > 0:
        mutated_sequence.extend([overlap, merged_string, str1.replace(overlap, ''), str2.replace(overlap, '')])
    else:
        mutated_sequence.extend(shorten_sequence(str1, extend_length))
        mutated_sequence.extend(shorten_sequence(str2, extend_length))
        mutated_sequence.extend(extend_sequence(str1, extend_length, text))
        mutated_sequence.extend(extend_sequence(str2, extend_length, text))
    for element in mutated_sequence:
        if len(element) < bits * size_bounds[0] or len(element) > bits * size_bounds[1] or element[0] in string.digits:
            mutated_sequence.remove(element)
    return mutated_sequence


def nextPopulation(population_size, population, size_bounds, text, diversity=0.01, bits=3):
    frequencies = count_frequency(population, text)
    filtered_pop, filtered_frequency = filter_by_freq(population, frequencies)
    sorted_pop = [x for _, x in sorted(zip(filtered_frequency, filtered_pop), reverse=True)]
    # wordPool = selection(population, frequencies)
    wordPool = selection(filtered_pop, filtered_frequency)
    newPopulation = []

    newPopulation.extend(sorted_pop[int(diversity * len(sorted_pop)):])

    while len(newPopulation) < population_size - int(diversity * len(sorted_pop)):
        try:
            parents = random.sample(wordPool, k=2)
            mutatedWords = mutation(parents[0], parents[1], size_bounds, text)
            newPopulation.extend(mutatedWords)
        except IndexError:
            pass
        except:
            parent = random.choice(wordPool)
            newPopulation.extend(shorten_sequence(parent, 10))
            newPopulation.extend(extend_sequence(parent, 10, text))

    newPopulation = [x for x in newPopulation if x]
    for p in newPopulation:
        if len(p) < bits * size_bounds[0] or len(p) > size_bounds[1] * bits:
            newPopulation.remove(p)

    newPopulation = list(set(newPopulation))

    while len(newPopulation) < population_size:
        individual = create_individual(text, size_bounds)
        if individual not in newPopulation:
            newPopulation.append(individual)
    return list(set(newPopulation))


def find_non_overlapping_strings(strings, frequency, bits=3):
    frequency_dict = {}
    for s, f in zip(strings, frequency):
        if f > 1:
            frequency_dict[s] = f
    strings = list(frequency_dict.keys())
    strings.sort(key=lambda x: (-frequency_dict.get(x, 0), -len(x)))
    non_overlapping = []
    for s1 in strings:
        overlap_found = False
        for s2 in non_overlapping:
            # Check for partial overlap
            if any(s1[i:] == s2[:len(s1) - i] for i in range(0, min(len(s1), len(s2)), bits)):
                overlap_found = True
                break
            if any(s2[i:] == s1[:len(s2) - i] for i in range(0, min(len(s1), len(s2)), bits)):
                overlap_found = True
                break
        if not overlap_found:
            non_overlapping.append(s1)
    return non_overlapping
