# class to store species data. Experiment will create a 2D list of species, where index is a generation, and at each generation is a list of species
class Specie:
    def __init__(self, id_num, count):
        # id number to distinguis individual species
        self.id_num = int(id_num)
        # count from xml file indicating the number of chromosomes within that species
        self.count = int(count)
        # list of chromosomes, stored as tuples(id_num, fitness)
        self.chromosomes = []

    # takes an id number and a fitness value and adds a chromosome tuple to the list of chromosomes, self.chromosomes
    def add_chromosome(self, id_num, fitness):
        self.chromosomes.append((int(id_num), int(fitness)))

    # takes an id number and returns the corresponding chromosome tuple
    def get_chromosome(self, id_num):
        for chromosome in self.chromosomes:
            if chromosome[0] == id_num:
                return chromosome

    # takes no arguments, returns the greatest fitness value from self.chromosomes
    def get_max_chromosome_fitness(self):
        max_val = 0
        for chromosome in self.chromosomes:
            if chromosome[1] > max_val:
                max_val = chromosome[1]
        return max_val

    # takes no arguments, calculates and returns the average fitness of the chromosomes in this species
    def get_avg_chromosome_fitness(self):
        total_fit = 0
        for chromosome in self.chromosomes:
            total_fit += chromosome[1]
        average = float(total_fit/len(self.chromosomes))
        return average

    # takes no arguments, returns the minimum fitness of the chromosomes in this species
    def get_min_chromosome_fitness(self):
        min_fit = self.chromosomes[0][1]
        for chromosome in self.chromosomes:
            if chromosome[1] < min_fit:
                min_fit = chromosome[1]
        return min_fit
