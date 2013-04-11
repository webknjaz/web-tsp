#!/usr/bin/env python3
import sys, random
from math import sqrt
from pickle import *

PIL_SUPPORT = None
try:
   from PIL import Image, ImageDraw, ImageFont
   PIL_SUPPORT = True
except:
   PIL_SUPPORT = False 

def longest_first(fst, lst):
    """Compare the length of one string to another, shortest goes first"""
    def cmp(a, b): 
        return (a > b) - (a < b)
    return cmp(lst.score, fst.score)

def cmp_to_key(mycmp):
    'Convert a cmp= function into a key= function'
    class K:
        def __init__(self, obj, *args):
            self.obj = obj 
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0 
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0 
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0   
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K

def cartesian_matrix(coords):
   """ A distance matrix """
   matrix = {}
   for i, (x1, y1) in enumerate(coords):
      for j, (x2, y2) in enumerate(coords):
         dx, dy = x1 - x2, y1 - y2
         dist = sqrt(dx * dx + dy * dy)
         matrix[i, j] = dist
   #print(len(matrix))
   #for line in matrix:
   #    print(line)
   return matrix 

def tour_length(matrix, tour):
   """ Returns the total length of the tour """
   total = 0
   num_cities = len(tour)
   #print(len(tour),tour)
   for i in range(num_cities):
      j = (i + 1) % num_cities
      city_i = tour[i]
      city_j = tour[j]
      #print((city_i, city_j))
      total += matrix[city_i, city_j]
   return total

def write_tour_to_img(coords, tour, img_file):
   """ The function to plot the graph """
   padding = 20
   coords = [(x + padding, y + padding) for (x, y) in coords]
   maxx, maxy = 0, 0
   for x, y in coords:
      maxx = max(x, maxx)
      maxy = max(y, maxy)
   maxx += padding
   maxy += padding
   img = Image.new("RGB", (int(maxx), int(maxy)),\
         color=(255, 255, 255))
   font = ImageFont.load_default()
   d = ImageDraw.Draw(img);
   num_cities = len(tour)
   for i in range(num_cities):
      j = (i + 1) % num_cities
      city_i = tour[i]
      city_j = tour[j]
      x1, y1 = coords[city_i]
      x2, y2 = coords[city_j]
      d.line((int(x1), int(y1), int(x2), int(y2)), fill=(0, 0, 0))
      d.text((int(x1) + 7, int(y1) - 5), str(i), \
        font=font, fill=(32, 32, 32)) 

   for x, y in coords:
      x, y = int(x), int(y)
      d.ellipse((x - 5, y - 5, x + 5, y + 5), outline=(0, 0, 0),\
                fill=(196, 196, 196))
   del d
   img.save(img_file, "PNG")
   if __name__ == '__main__':
       print("The plot was saved into the %s file." % (img_file,))  

cm = []
coords = [] 

def eval_func(chromosome, _cm = None):
   """ The evaluation function """
   if _cm is None:
      global cm
      _cm = cm
   return tour_length(_cm, chromosome) 

def cities_random(cities, xmax=800, ymax=600):
   """ get random cities/positions """
   coords = []
   for i in range(cities):
      x = random.randint(0, xmax)
      y = random.randint(0, ymax)
      coords.append((float(x), float(y)))
   return coords

#Individuals
class Individual:
    score = 0
    #length = 30
    seperator = ' '
    def __init__(self, chromosome=None, length=30, cm = None):
        #print('cm len is', len(cm), '. chromosome len is', len(chromosome))
        self.cm = cm
        self.length = len(chromosome) if length is None else length
        self.chromosome = chromosome or self._makechromosome()
        self.score = 0  # set during evaluation  

    def _makechromosome(self):
        "makes a chromosome from randomly selected alleles."
        chromosome = []
        lst = [i for i in range(self.length)]
        for i in range(self.length):
            choice = random.choice(lst)
            lst.remove(choice)
            chromosome.append(choice)
        return chromosome

    def evaluate(self, optimum=None, cm = None):
        #print(self.chromosome, cm)
        self.score = eval_func(self.chromosome, _cm = cm)

    def crossover(self, other):
        left, right = self._pickpivots()
        p1 = Individual(cm = self.cm, length = self.length)
        p2 = Individual(cm = self.cm, length = self.length)
        c1 = [ c for c in self.chromosome \
               if c not in other.chromosome[left:right + 1]]
        p1.chromosome = c1[:left] + other.chromosome[left:right + 1]\
                         + c1[left:]
        c2 = [ c for c in other.chromosome \
               if c not in self.chromosome[left:right + 1]]
        p2.chromosome = c2[:left] + self.chromosome[left:right + 1] \
                        + c2[left:]
        return p1, p2

    def mutate(self):
        "swap two element"
        left, right = self._pickpivots()
        temp = self.chromosome[left]
        self.chromosome[left] = self.chromosome[right]
        self.chromosome[right] = temp   

    def _pickpivots(self):
        left = random.randint(0, self.length - 2)
        right = random.randint(left, self.length - 1)
        return left, right    

    def __repr__(self):
        "returns string representation of self"
        return '<%s chromosome="%s" score=%s>' % \
               (self.__class__.__name__,
                self.seperator.join(map(str, self.chromosome)), self.score)  

    def copy(self):
        twin = self.__class__(self.chromosome[:])
        twin.score = self.score
        return twin

    def __cmp__(self, other):
        return cmp(self.score, other.score)

    def toPlainObject(self):
        return {
                'path': [int(Dot) for Dot in map(str, self.chromosome)],
                'score': self.score
                }

class Environment:
    size = 0
    def __init__(self, population=None, size=None, maxgenerations=1000,\
                 newindividualrate=0.6,crossover_rate=0.90,\
                 mutation_rate=0.1,\
                 cm=None):
        #print('cm len is', len(cm))
        self.cm = cm
        self.size = size if size is not None else 100
        self.population = self._makepopulation()
        self.maxgenerations = maxgenerations
        self.newindividualrate = newindividualrate
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        for individual in self.population:
            individual.evaluate(cm = self.cm)
        self.generation = 0
        self.minscore = sys.maxsize
        self.minindividual = None
        #self._printpopulation()
        if PIL_SUPPORT:
            write_tour_to_img(coords, self.population[0].chromosome,\
                              "TSPstart.png")
        else:
            if __name__ == '__main__':
                print("No PIL detected,can not plot the graph")

    def _makepopulation(self):
        return [Individual(cm = self.cm, length = self.size) for i in range(0, self.size)]

    def run(self):
        for i in range(1, self.maxgenerations + 1):
            if __name__ == '__main__':
                print("Generation no:" + str(i))
            for j in range(0, self.size):
                self.population[j].evaluate(cm = self.cm)
                curscore = self.population[j].score
                if curscore < self.minscore:
                    self.minscore = curscore
                    self.minindividual = self.population[j]
            if __name__ == '__main__':
                print("Best individual:", self.minindividual)
            if random.random() < self.crossover_rate:
                children = []
                newindividual = int(self.newindividualrate * self.size / 2)
                for i in range(0, newindividual):
                    selected1 = self._selectrank()
                    selected2 = self._selectrank()
                    parent1 = self.population[selected1]
                    parent2 = self.population[selected2]
                    child1, child2 = parent1.crossover(parent2)
                    child1.evaluate(cm = self.cm)
                    child2.evaluate(cm = self.cm)
                    children.append(child1)
                    children.append(child2)
                for i in range(0, newindividual):
                    #replce with child
                    totalscore = 0
                    for k in range(0, self.size):
                        totalscore += self.population[k].score
                    randscore = random.random()
                    addscore = 0
                    for j in range(0, self.size):
                        addscore += (self.population[j].score / totalscore)
                        if addscore >= randscore:
                            self.population[j] = children[i]
                            break
            if random.random() < self.mutation_rate:
                selected = self._select()
                self.population[selected].mutate()
        #end loop
        for i in range(0, self.size):
                self.population[i].evaluate(cm = self.cm)
                curscore = self.population[i].score
                if curscore < self.minscore:
                    self.minscore = curscore
                    self.minindividual = self.population[i]
        if __name__ == '__main__':
            print("..................Result.........................")
            print(self.minindividual)
            #self._printpopulation()
        return self.minindividual

    def _select(self):
        totalscore = 0
        for i in range(0, self.size):
            totalscore += self.population[i].score
        randscore = random.random()*(self.size - 1)
        addscore = 0
        selected = 0
        for i in range(0, self.size):
            addscore += (1 - self.population[i].score / totalscore)
            if addscore >= randscore:
                selected = i
                break
        return selected

    def _selectrank(self, choosebest=0.9):
        self.population.sort(key=cmp_to_key(longest_first))
        rand_start = int(self.size * self.newindividualrate)
        rand_end = int(self.size - 1)
        if random.random() < choosebest:
            return random.randint(0, rand_start)
        else:
            return random.randint(rand_start, rand_end)

    def _printpopulation(self):
        for i in range(0, self.size):
            print("Individual ", i, self.population[i])      

def main_run():
    global cm, coords
    #get cities's coords
    s = 10
    coords =cities_random(s)
    cm = cartesian_matrix(coords)
    ev = Environment(cm = cm, size = s)
    ev.run()
    if PIL_SUPPORT:
        write_tour_to_img(coords, ev.minindividual.chromosome, \
                          "TSPresult.png")
    else:
        if __name__ == '__main__':
            print("No PIL detected,can not plot the graph")
if __name__ == "__main__":
    main_run()
