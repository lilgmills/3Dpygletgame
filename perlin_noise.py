from noise import pnoise2
import numpy as np
from math import floor, ceil

def perlin_array(shape = (1200, 600), amplitude = 1,
			scale = 160,octaves = 5,
                        persistence = 0.73,
                        lacunarity= 2.3, 
			seed = None):

    if not seed:

        seed = np.random.randint(0, 100)
        print("seed was {}".format(seed))

    arr = np.zeros(shape)
    for i in range(shape[0]):
        for j in range(shape[1]):
            arr[i][j] = pnoise2(i / scale,
                                        j / scale,
                                        octaves=octaves,
                                        persistence=persistence,
                                        lacunarity=lacunarity,
                                        repeatx=1024,
                                        repeaty=1024,
                                        base=seed)
    max_arr = np.max(arr)
    min_arr = np.min(arr)
    norm_me = lambda x: floor(((x-min_arr)/(max_arr - min_arr))* 3*amplitude)/3
    norm_me = np.vectorize(norm_me)
    arr = norm_me(arr)
    return arr

if __name__ == "__name__":
    arr = perlin_array()

    filter = perlin_array(shape = (1200,600),
                          scale = 800, octaves = 3,
                          persistence = 0.8,
                          lacunarity = 1)

    with open("tile_codes/digital_codes.txt", "w+") as f:
        for line_i in range (arr.shape[0]):
            for perlin_val_j in range(arr.shape[1]):
                perlin_val = arr[line_i, perlin_val_j]
                
                norm = lambda p_v: max(floor(p_v*5),0)            
                
                
                perlin_filter = filter[line_i, perlin_val_j]

                perlin_filter = perlin_val * (6*perlin_filter**5 - 15*perlin_filter**4 + 10* perlin_filter**3)*2

                perlin_filter = norm(perlin_filter)
                
                f.write(str(perlin_filter)+",")
            f.write("\n")
