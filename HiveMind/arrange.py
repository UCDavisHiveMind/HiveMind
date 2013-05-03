import random
random.seed(77)

#- define number of nodes to use
X_SZ = 15
Y_SZ = 15
LAST_ROUND = 50
STOP_THRESH = 0.00001

class node:

    #- (1) nodes are placed in a cell in a grid, nodes are moved/assigned to grid locations to support proximity-similarity
    #- (2) nodes are assigned a fixed number of arbitrary neighbors, nodes auction to swap neighbors to support proximity-similarity
    
    def __init__(self, name, x, y):
        self.name = name
        self.ref = "%s:%s" % (x, y)
        self.neighbors = {'up':{'idx':None}, 'ur':{'idx':None}, 'rt':{'idx':None}, 'dr':{'idx':None},
                          'dn':{'idx':None}, 'dl':{'idx':None}, 'lt':{'idx':None}, 'ul':{'idx':None}}
        
        self.neighbors['up']['idx'] = "%s:%s" % self.neighbor_up(x, y)
        self.neighbors['ur']['idx'] = "%s:%s" % self.neighbor_ur(x, y)
        self.neighbors['rt']['idx'] = "%s:%s" % self.neighbor_rt(x, y)
        self.neighbors['dr']['idx'] = "%s:%s" % self.neighbor_dr(x, y)
        self.neighbors['dn']['idx'] = "%s:%s" % self.neighbor_dn(x, y)
        self.neighbors['dl']['idx'] = "%s:%s" % self.neighbor_dl(x, y)
        self.neighbors['lt']['idx'] = "%s:%s" % self.neighbor_lt(x, y)
        self.neighbors['ul']['idx'] = "%s:%s" % self.neighbor_ul(x, y)
        
        self.attribs = (random.random(), random.random())
        
        self.cur_max_neighbor_value = 0
        self.cur_max_neighbor_dir = None

    def coords(self, x, y, dx, dy):
        x = (x + X_SZ + dx) % X_SZ
        y = (y + Y_SZ + dy) % Y_SZ
        return (x, y)
    
    def neighbor_up(self, x, y):
        (x, y) = self.coords(x, y, 0, -1)
        return (x, y)
    
    def neighbor_ur(self, x, y):
        (x, y) = self.coords(x, y, +1, -1)
        return (x, y)
    
    def neighbor_rt(self, x, y):
        (x, y) = self.coords(x, y, +1, 0)
        return (x, y)
    
    def neighbor_dr(self, x, y):
        (x, y) = self.coords(x, y, +1, +1)
        return (x, y)
    
    def neighbor_dn(self, x, y):
        (x, y) = self.coords(x, y, 0, +1)
        return (x, y)
    
    def neighbor_dl(self, x, y):
        (x, y) = self.coords(x, y, -1, +1)
        return (x, y)
    
    def neighbor_lt(self, x, y):
        (x, y) = self.coords(x, y, -1, 0)
        return (x, y)
    
    def neighbor_ul(self, x, y):
        (x, y) = self.coords(x, y, -1, -1)
        return (x, y)

    def calc_diff_to_neighbor(self, direction):
        #diff_value = self.calc_diff(self.attribs, self.attribs)
        diff_value = self.calc_diff(self.attribs, nodes[self.neighbors[direction]['idx']].attribs)
        #print "%s: diff:[%s] = %s" % (self.name, direction, diff_value)
        self.neighbors[direction]['sim'] = diff_value
        return diff_value
        
    def least_similar_neighbor(self):
        self.cur_max_neighbor_value = 0
        for d in self.neighbors:            
            if self.calc_diff_to_neighbor(d) > self.cur_max_neighbor_value:
                self.cur_max_neighbor_value = self.neighbors[d]['sim']
                self.cur_max_neighbor_dir = d
                self.most_different_neighbor = self.neighbors[d]['idx']

        return (self.most_different_neighbor, self.cur_max_neighbor_dir, self.cur_max_neighbor_value)    

    #- define difference function
    def calc_diff(self, local_attribs, neighbor_attribs):
        diff_value = (local_attribs[0] - neighbor_attribs[0]) ** 2 + (local_attribs[1] - neighbor_attribs[1]) ** 2
        return diff_value
    
    
    
    def consider_offer(self, offered):       
        
        #- see if the offered node is ourself
        if offered == self.ref:
            ##print "        !>> node %s is ourself [%s]" % (offered, self.ref)
            return []
        
        #- see if the offered node is already used here
        if offered in [self.neighbors[d]['idx'] for d in self.neighbors] or offered == self.ref:
            ##print "        !>> node %s already used here [%s]" % (offered, self.ref)
            return []
        
        #- see if this is of any value, and if so which you'd like to swap
        diff = self.calc_diff(self.attribs, nodes[offered].attribs) #- get diff to object
        
        #- get list of neighbors that have a diff worse than what is offered
        offer_list = [self.neighbors[d]['idx'] for d in self.neighbors if self.calc_diff_to_neighbor(d) > diff]
        #offer_list = [self.least_similar_neighbor()[0]]
        
        #- return the
        return offer_list
    
             
            
    def swap_neighbors(self, new_neighbor, old_neighbor, offerrer):
        
        #- find the direction corresponding to the our neighbor to swap
        swapped = False
        for d in self.neighbors:
            if self.neighbors[d]['idx'] == old_neighbor:
                ##print "***** SWAPPING NEIGHBORS: on %s, %s --> %s" % (self.ref, old_neighbor, new_neighbor)
                self.neighbors[d]['idx'] = new_neighbor
                self.least_similar_neighbor()  #- update who is now least similar
                swapped = True

        if swapped is False:
            #- ??? neighbor not found
            print "ERROR: swapping on self -- %s not a neighbor of %s" % (old_neighbor, self.ref)
            return False

        #- find the direction corresponding to the our neighbor to swap
        swapped = False
        for d in nodes[new_neighbor].neighbors:
            if nodes[new_neighbor].neighbors[d]['idx'] == offerrer:
                nodes[new_neighbor].neighbors[d]['idx'] = self.ref
                ##print "***** SWAPPING NEIGHBORS: on %s, %s --> %s" % (new_neighbor, offerrer, self.ref)
                nodes[new_neighbor].least_similar_neighbor()  #- update who is now least similar
                swapped = True
                
        if swapped is False:
            #- ??? neighbor not found
            print "ERROR:  swapping on new neighbor -- %s not a neighbor of %s" % (offerrer, new_neighbor)
            return False
        
        return True
        
    
    def auction_worst_neighbor(self):
        best_offer = self.cur_max_neighbor_value  #- initialize to current worst
        best_offer_node = None
        best_offerer = None
        
        print "\nactive: %s> offering = %s [%s]" % (self.name, self.most_different_neighbor, self.cur_max_neighbor_value)
            
        #- make offer to all others
        #- accept the best offer
        knt = 0
        for x in range(0, X_SZ):
            for y in range(0, Y_SZ):
                knt += 1    
                ref = "%s:%s" % (x, y)

                #- don't make offer to self
                if ref == self.ref: continue
                
                #- don't make offer to same node as being offered 
                if ref == self.most_different_neighbor: continue 
                
                #- make offer and see what that node will give in exchange
                offer_list = nodes[ref].consider_offer(self.most_different_neighbor)
                print "---> [%s]" % (', '.join(offer_list))
                if offer_list == []:
                    #- no offer made, skip
                    ##print "        w/ %s>> made no offer for %s" % (ref, self.most_different_neighbor)
                    continue

                for will_give in offer_list:                 
                    #- ignore offers of ourself or for neighbors this node already has
                    if will_give == self.ref:
                        ##print "    %s> offered ourself" % (ref)
                        continue
                    elif will_give in [self.neighbors[d]['idx'] for d in self.neighbors]:
                        ##print "    %s> offered existing neighbor" % (ref)
                        continue
                    else:
                        #- offer was made, is it the best?
                        dv = self.calc_diff(self.attribs, nodes[will_give].attribs)
                        ##print "    %s> offered %s for our %s [our diff for offer=%6.4f]" % (ref, will_give, self.most_different_neighbor, dv)
    
                        value = self.calc_diff(self.attribs, nodes[will_give].attribs)
                        if value < best_offer:
                            best_offer = value
                            best_offer_node = will_give
                            best_offerer = ref
                            print "       w/ %s >> tentatively exchanging %s (%s) for %s (%s)" % (ref, self.most_different_neighbor, self.cur_max_neighbor_value, best_offer_node, best_offer)
        
        #- if any accepted offers, swap neighbors now
        if best_offerer is not None:
            my_offerred_node = self.most_different_neighbor
            my_largest_diff = self.cur_max_neighbor_value
            
            #- swap out your worst neighbor with the best offered node
            self.swap_neighbors(best_offer_node, my_offerred_node, best_offerer)
            
            #- tell other node to swap the neighbor node it offered for the one you offered
            nodes[best_offerer].swap_neighbors(my_offerred_node, best_offer_node, self.ref)

            generate_dot_graph('/home/steven/neighbor_graph-r%d.%d.dot' % (round_number, knt))

            print "%s>> exchanged %s (%s) for %s (%s) -- on %s" % (self.ref, my_offerred_node, my_largest_diff, best_offer_node, best_offer, best_offerer)
            ##print "    >> new worst: %s, new diff:%6.4f" % (self.most_different_neighbor, self.cur_max_neighbor_value)
        else:
            ##print "%s>> no exchange made" % (self.ref)       
            pass


def calc_overall_similarity():
    o_sim = 0.0
    max_single_diff = 0.0
    max_node_diff = 0.0
    for x in range(0, X_SZ):
        for y in range(0, Y_SZ):
            
            ref = "%s:%s" % (x, y)

            #- get diffs for neighbors of this node            
            node_sims = [nodes[ref].calc_diff_to_neighbor(i) for i in ['up', 'ur', 'rt', 'dr', 'dn', 'dl', 'lt', 'ul']]
            
            #- update max if needed
            mx = max(node_sims)
            if mx > max_single_diff: max_single_diff = mx
            
            #- get sum of diffs for this node
            sum_of_diffs = 0
            for i in node_sims: sum_of_diffs += i 
            
            #- update max if needed
            if sum_of_diffs > max_node_diff: max_node_diff = sum_of_diffs
            
            
            #node_sim += nodes[ref].calc_diff_to_neighbor('up')
            #node_sim += nodes[ref].calc_diff_to_neighbor('ur')
            #node_sim += nodes[ref].calc_diff_to_neighbor('rt')
            #node_sim += nodes[ref].calc_diff_to_neighbor('dr')
            #node_sim += nodes[ref].calc_diff_to_neighbor('dn')
            #node_sim += nodes[ref].calc_diff_to_neighbor('dl')
            #node_sim += nodes[ref].calc_diff_to_neighbor('lt')
            #node_sim += nodes[ref].calc_diff_to_neighbor('ul')
            
            #- add to overall sum
            o_sim += sum_of_diffs
    
    #- divide by number of nodes ( = average node diff sum)        
    o_sim = o_sim / (Y_SZ * X_SZ)         
    
    return o_sim, max_node_diff, max_single_diff
    

def generate_dot_graph(fname):
    f = open(fname, 'w')    
    f.write("digraph G {\n")
    
    for x in range(0, X_SZ):
        for y in range(0, Y_SZ):
            ref = "%s:%s" % (x, y)
            for i in ['up', 'ur', 'rt', 'dr', 'dn', 'dl', 'lt', 'ul']:
                n = nodes[ref].neighbors[i]['idx']
                (nx, ny) = n.split(':')
                f.write("    \"(%d,%d)\" -> \"(%d,%d)\";" % (x, y, int(nx), int(ny)))
                 
    f.write("}\n")
    f.close()
        



#--------------------------------------------------------------------------------------------------
#- Initialize attributes for all nodes
#--------------------------------------------------------------------------------------------------
nodes = {}
for x in range(0, X_SZ):
    for y in range(0, Y_SZ):      
        ref = "%s:%s" % (x, y)
        nodes[ref] = node('node-' + ref, x, y)        

#--------------------------------------------------------------------------------------------------
#- calculate initial differences between each node and its neighbors
#--------------------------------------------------------------------------------------------------
for x in range(0, X_SZ):
    for y in range(0, Y_SZ):
        
        ref = "%s:%s" % (x, y)
        nodes[ref].calc_diff_to_neighbor('up')
        nodes[ref].calc_diff_to_neighbor('ur')
        nodes[ref].calc_diff_to_neighbor('rt')
        nodes[ref].calc_diff_to_neighbor('dr')
        nodes[ref].calc_diff_to_neighbor('dn')
        nodes[ref].calc_diff_to_neighbor('dl')
        nodes[ref].calc_diff_to_neighbor('lt')
        nodes[ref].calc_diff_to_neighbor('ul')
        (n, d, v) = nodes[ref].least_similar_neighbor()
        #print "%s--> [%s] = %s (%s)" % (ref, n, v, d)

generate_dot_graph('/home/steven/neighbor_graph-init.dot')

#--------------------------------------------------------------------------------------------------
#-  repeat rounds until max iterations or average 
#-   similarity is not significantly changing
#--------------------------------------------------------------------------------------------------
(o_sim, mxnd, mxnbr) = calc_overall_similarity()
o_sim_last = o_sim + 1
print "overall similarity metric: %6.4f (node: %6.4f, nbr:%6.4f)" % (o_sim, mxnd, mxnbr)

round_number = 0
while round_number < LAST_ROUND and abs(o_sim_last - o_sim) > STOP_THRESH:
    
    ##print "\n\n\n===================================================================="
    print "-- Round %d -------------------" % (round_number)
    for x in range(0, X_SZ):
        for y in range(0, Y_SZ):
            ref = "%s:%s" % (x, y)
            
            #- announce auction for 'n'
            result = nodes[ref].auction_worst_neighbor()
            ##print ">>>> result=", result
    
    o_sim_last = o_sim
    (o_sim, mxnd, mxnbr) = calc_overall_similarity()
    print "%4d - overall similarity metric: %6.4f (was %6.4f) -- (node: %6.4f, nbr:%6.4f)" % (round_number, o_sim, o_sim_last, mxnd, mxnbr)

    generate_dot_graph("/home/steven/neighbor_graph-r%s.dot" % (round_number))

    round_number += 1        


for x in range(0, X_SZ):
    for y in range(0, Y_SZ):
         
        ref = "%s:%s" % (x, y)

        #- get diffs for neighbors of this node            
        node_sims = [nodes[ref].calc_diff_to_neighbor(i) for i in ['up', 'ur', 'rt', 'dr', 'dn', 'dl', 'lt', 'ul']]
                  
        #- get sum of diffs for this node
        sum_of_diffs = 0
        for i in node_sims: sum_of_diffs += i 
        
        print "%s: %6.4f" % (ref, sum_of_diffs)

generate_dot_graph('/home/steven/neighbor_graph-final.dot')
             
        
print "DONE"
