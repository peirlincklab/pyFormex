/* */
//
//  SPDX-FileCopyrightText: © 2007-2023 Benedict Verhegghe <bverheg@gmail.com>
//  SPDX-License-Identifier: GPL-3.0-or-later
//
//  This file is part of pyFormex 3.3  (Sun Mar 26 20:16:15 CEST 2023)
//  pyFormex is a tool for generating, manipulating and transforming 3D
//  geometrical models by sequences of mathematical operations.
//  Home page: https://pyformex.org
//  Project page: https://savannah.nongnu.org/projects/pyformex/
//  Development: https://gitlab.com/bverheg/pyformex
//  Distributed under the GNU General Public License version 3 or later.
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.
//
//  This program is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU General Public License for more details.
//
//  You should have received a copy of the GNU General Public License
//  along with this program.  If not, see http://www.gnu.org/licenses/.
//

#include <Python.h>
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <numpy/arrayobject.h>
#include <stdio.h>

// cast pointers to avoid warnings
#define PYARRAY_DATA(p) PyArray_DATA((PyArrayObject *)p)
#define PYARRAY_DIMS(p) PyArray_DIMS((PyArrayObject *)p)
#define PYARRAY_FROM_OTF(p,q,r) (PyArrayObject *) PyArray_FROM_OTF(p,q,r)

#define print PySys_WriteStderr


/****************** LIBRARY VERSION AND DOCSTRING *******************/

static char *__version__ = "3.4.dev0";
static char *__doc__ = "\
Accelerated cluster optimization\n\
\n\
This module provides compiled C clustering functions.\n\
These functions are not intended for the end user. They are called\n\
internally by other pyFormex functions to speed up their operation.\n\
";

typedef unsigned char uint8;


#ifdef DEBUG

static int max(int *clusters, int npoints)
{
    int m = 0;
    for (int i=0; i<npoints; ++i)
	if (clusters[i] > m)
	    m = clusters[i];
    return m;
}


static int min(int *clusters, int npoints)
{
    int m = 999999;
    for (int i=0; i<npoints; ++i)
	if (clusters[i] < m)
	    m = clusters[i];
    return m;
}


static void print_clusters(char *s, int *clusters, int npoints)
{
    int mi, ma, i, l;
    char buf[81];
    int width, total;
    char *format;

    mi = min(clusters, npoints);
    ma = max(clusters, npoints);
    print("Clusters @ %s: n=%d, min=%d, max=%d\n", s, npoints, mi, ma);
    l = 0;
    if (npoints < 100) {
	width = 3;
	total = 72;
	format = "%3d";
    } else {
	width = 4;
	total = 72;
	format = "%4d";
    }
    for (i=0; i<npoints; ++i) {
	sprintf(buf+l, format, clusters[i]);
	l += width;
	if (l >= total) {
	    buf[l] = 0;
	    print("%s\n", buf);
	    l = 0;
	    buf[l] = 0;
	}
    }
    if (l > 0)
	print("%s\n", buf);
}
#endif

/**************************************************** init_clusters ****/
/* Initialize clusters */
/* args:
   int clusters (npoints)
   int neigh (npoints, maxneigh)
   int nneigh (npoints)
   float area (npoints)
   int nclus
   int npoints
   int maxneigh
*/
static void init_clusters(int *clusters, int *neigh, int *nneigh,
			  float *area, int nclus, int npoints, int maxneigh)
{
    float tarea, carea;
    int item;
    int i, j, k, checkitem, c, c_prev;
    float ctarea;
    int lstind = 0;
    int i_items_new, i_items_old;

    int *items = calloc(npoints*2, sizeof(int));

    /* Initialize clusters */
    for (i=0; i<npoints; ++i)
	clusters[i] = -1;

    /* Total mesh size */
    float area_remain = 0;
    for (i=0; i<npoints; ++i)
        area_remain += area[i];

    /* Assign clusters */
    ctarea = area_remain/nclus;
    for (i=0; i<nclus; ++i) {
        /* Get target area and reset current area */
        tarea = area_remain - ctarea*(nclus - i - 1);
        carea = 0.0;

        /* Get starting index (the first free face in list) */
        i_items_new = 0;
	for (j=lstind; j<npoints; ++j) {
            if (clusters[j] == -1) {
                carea += area[j];
                items[0] = j;
                clusters[j] = i;
                lstind = j;
                break;
	    }
	}

        if (j == npoints)
            break;

        /* While there are new items to be added */
        c = 1;
        while (c) {

            /* reset items */
            c_prev = c;
            c = 0;
            /* switch indices */
            if (i_items_new == 0) {
                i_items_old = 0;
                i_items_new = 1;
	    } else {
                i_items_old = 1;
                i_items_new = 0;
	    }

            /* progressively add neigh */
            for (j=0; j<c_prev; ++j) {
                checkitem = items[j*2+i_items_old];
		for (k=0; k<nneigh[checkitem]; ++k) {
		    item = neigh[maxneigh*checkitem+k];

                    /* check if the face is free */
                    if (clusters[item] == -1) {
                        /* if allowable, add to cluster */
                        if (area[item] + carea < tarea) {
                            carea += area[item];
                            clusters[item] = i;
                            items[c*2+i_items_new] = item;
                            c += 1;
			}
		    }
		}
	    }
	}
        area_remain -= carea;
    }
    free(items);
}


/**************************************************** grow_null ****/
/* Grow clusters to include null faces */
/* args:
   int clusters (npoints): cluster number for the points
   int edges (nedges,2): edge definitions
   int nedges
*/

static void grow_null(int *clusters, int *edges, int nedges)
{
    int i, face_a, face_b, clusA, clusB, nchange;

    nchange = 1;
    while (nchange > 0) {
	nchange = 0;
	/* Determine edges that share two clusters */
	for (i=0; i<nedges; ++i) {
	    /* Get the two clusters sharing an edge */
	    face_a = edges[2*i];
	    face_b = edges[2*i+1];
	    clusA = clusters[face_a];
	    clusB = clusters[face_b];
	    /* Check and immediately flip a cluster edge
	       if one is part of the null cluster */
	    if (clusA == -1 && clusB != -1) {
		clusters[face_a] = clusB;
		nchange += 1;
	    } else if (clusB == -1 && clusA != -1) {
		clusters[face_b] = clusA;
		nchange += 1;
	    }
	}
    }
}


/**************************************************** disconnected ****/
/* Remove isolated clusters */
/* args:
   int clusters (npoints)
   int neigh (npoints, maxneigh)
   int nneigh (npoints)
   int nclus
   int npoints
   int maxneigh
*/
static int disconnected(int *clusters, int *neigh, int *nneigh,
			int nclus, int npoints, int maxneigh)
{
    uint8 *visited = calloc(npoints, sizeof(uint8));
    uint8 *visited_cluster = calloc(nclus, sizeof(uint8));
    int *front = calloc(npoints*2, sizeof(int));
    int nclus_checked = 0;
    int lst_check = 0;
    int ndisc = 0;
    int ind, index, ifound, cur_clus, c, i_front_old, i_front_new, i, j, c_prev;

    /* fake init */
    for (i=0; i<npoints*2; ++i)
	front[i] = -3;

    ifound = -1;
    int cnt = 0;
    while (nclus_checked < nclus) {
	cnt += 1;

        /* seedpoint is first point available that has not been checked */
        for (i=lst_check; i<npoints; ++i) {
            /* if point and cluster have not been visited */
            if (!visited[i] && !visited_cluster[clusters[i]]) {
                ifound = i;
                lst_check = i;
                nclus_checked += 1;
                break;
	    }
        }
        /* restart if end of points reached */
        /* if (i == npoints - 1 || (debug && i == npoints)) { */
	if (i >= npoints-1) {
	    /* print("BREAK at i=%d, cnt=%d\n", i, cnt); */
            break;
	}

        /* store cluster data and check that this has been visited */
        cur_clus = clusters[ifound];
        visited[ifound] = 1;
        visited_cluster[cur_clus] = 1;

        /* if (debug) { */
        /*     print("nclus_checked: %d, lst_check: %d, ifound=%d, cur_clus=%d, i=%d, cnt=%d\n", nclus_checked, lst_check, ifound, cur_clus, i, cnt); */
	/* } */
        /* perform front expansion */
        i_front_new = 0;
        front[0] = ifound;
        c = 1;  /* dummy init to start while loop */
        while (c > 0) {

            /* reset front */
            c_prev = c;
            c = 0;
            /* switch indices */
            if (i_front_new == 0) {
                i_front_old = 0;
                i_front_new = 1;
	    } else {
                i_front_old = 1;
                i_front_new = 0;
	    }
            for (j=0; j<c_prev; ++j) {
                ind = front[2*j+i_front_old];
                for (i=0; i<nneigh[ind]; ++i) {
                    index = neigh[maxneigh*ind+i];
                    if (clusters[index] == cur_clus && !visited[index]) {
                        front[2*c+i_front_new] = index;
                        c += 1;
                        visited[index] = 1;
		    }
		}
	    }
	}
    }
    /* Finally, null any points that have not been visited */
    ndisc = 0;
    for (i=0; i<npoints; ++i) {
        if (!visited[i]) {
	    /* print("Isolated point %d: %d\n", ndisc, i); */
            clusters[i] = -1;
            ndisc += 1;
	}
    }
    /* free allocations */
    free(visited);
    free(visited_cluster);
    free(front);

    return ndisc;
}


/**************************************************** minimize_energy ****/
/* Minimize cluster energy */
/* args:
   int edges (nedges, 2)
   int clusters (npoints,)
   float area (npoints,)
   float sgamma (nclus, 3)
   float cent (nvert, 3)
   float srho (nclus,)
   int cluscount(nclus,)
   float energy (nclus,)
   int nedges
   int nclus
   int maxiter
*/

static void minimize_energy(int *edges, int *clusters, float *area,
			    float *sgamma, float *cent, float *srho,
			    int *cluscount, float *energy,
			    int nedges, int nclus, int maxiter)
{
    int face_a, face_b, clusA, clusB;
    float areaface_a, centA0, centA1, centA2;
    float areaface_b, centB0, centB1, centB2;
    float eA, eB, eorig, eAwB, eBnB, eAnA, eBwA;
    int nchange = 1;
    int niter = 0;
    int i;

    /* Allocate modified arrays */
    uint8 *mod1 = calloc(nclus, sizeof(uint8));
    uint8 *mod2 = calloc(nclus, sizeof(uint8));
    /* start all as modified */
    for (i=0; i<nclus; ++i)
	mod2[i] = 1;
    while (nchange > 0 && niter < maxiter) {
	/* print("minimize ITERATION %d\n", niter); */
	/* Reset modification arrays */
        for (i=0; i<nclus; ++i) {
            mod1[i] = mod2[i];
            mod2[i] = 0;
	}
        nchange = 0;
	for (i=0; i<nedges; ++i) {
            /* Get the two clusters sharing an edge */
            face_a = edges[2*i];
            face_b = edges[2*i+1];
            clusA = clusters[face_a];
            clusB = clusters[face_b];
	    /* If edge shares two different clusters and at least one
	       has been modified since last iteration */
            if (clusA != clusB && (mod1[clusA] == 1 || mod1[clusB] == 1)) {
		/* print("mod %d: %d, %d, %d, %d\n", */
		/*       i, face_a, face_b, clusA, clusB); */
                /* Verify that face can be removed from cluster */
                if (cluscount[clusA] > 1 && cluscount[clusB] > 1) {
		    /* Can be removed from both A and B */
                    areaface_a = area[face_a];
                    centA0 = cent[3*face_a];
                    centA1 = cent[3*face_a+1];
                    centA2 = cent[3*face_a+2];
                    areaface_b = area[face_b];
                    centB0 = cent[3*face_b];
                    centB1 = cent[3*face_b+1];
                    centB2 = cent[3*face_b+2];
                    /* Current energy */
                    eorig = energy[clusA] + energy[clusB];
                    /* Energy with both items assigned to cluster A */
                    eAwB = (pow(sgamma[3*clusA] + centB0, 2) +
                            pow(sgamma[3*clusA+1] + centB1, 2) +
                            pow(sgamma[3*clusA+2] + centB2, 2)) /
			(srho[clusA] + areaface_b);
		    eBnB = (pow(sgamma[3*clusB] - centB0, 2) +
                            pow(sgamma[3*clusB+1] - centB1, 2) +
                            pow(sgamma[3*clusB+2] - centB2, 2)) /
			(srho[clusB] - areaface_b);
                    eA = eAwB + eBnB;
		    /* Energy with both items assigned to clusterB */
                    eAnA = (pow(sgamma[3*clusA] - centA0, 2) +
                            pow(sgamma[3*clusA+1] - centA1, 2) +
                            pow(sgamma[3*clusA+2] - centA2, 2)) /
			(srho[clusA] - areaface_a);
                    eBwA = (pow(sgamma[3*clusB] + centA0, 2) +
                            pow(sgamma[3*clusB+1] + centA1, 2) +
                            pow(sgamma[3*clusB+2] + centA2, 2)) /
			(srho[clusB] + areaface_a);
                    eB = eAnA + eBwA;

                    /* select the largest case (most negative) */
                    if (eA > eorig && eA > eB) {
			/* Show clusters as modified */
                        mod2[clusA] = 1;
                        mod2[clusB] = 1;
                        nchange += 1;
			/* reassign */
                        clusters[face_b] = clusA;
                        cluscount[clusB] -= 1;
                        cluscount[clusA] += 1;
			/* Update cluster A mass and centroid */
                        srho[clusA] += areaface_b;
                        sgamma[3*clusA] += centB0;
                        sgamma[3*clusA+1] += centB1;
                        sgamma[3*clusA+2] += centB2;

                        srho[clusB] -= areaface_b;
                        sgamma[3*clusB] -= centB0;
                        sgamma[3*clusB+1] -= centB1;
                        sgamma[3*clusB+2] -= centB2;

                        /* Update cluster energy */
                        energy[clusA] = eAwB;
                        energy[clusB] = eBnB;
		    }
		    /* if the energy contribution of both to B is less
		       than the original and to cluster A */
                    else if (eB > eorig && eB > eA) {
			/* Show clusters as modified */
                        mod2[clusA] = 1;
                        mod2[clusB] = 1;
                        nchange += 1;
			/* reassign */
                        clusters[face_a] = clusB;
                        cluscount[clusA] -= 1;
                        cluscount[clusB] += 1;
                        /* Add item A to cluster B */
                        srho[clusB] += areaface_a;
                        sgamma[3*clusB] += centA0;
                        sgamma[3*clusB+1] += centA1;
                        sgamma[3*clusB+2] += centA2;
			/* Remove item A from cluster A */
                        srho[clusA] -= areaface_a;
                        sgamma[3*clusA] -= centA0;
                        sgamma[3*clusA+1] -= centA1;
                        sgamma[3*clusA+2] -= centA2;
                        /* Update cluster energy */
                        energy[clusA] = eAnA;
                        energy[clusB] = eBwA;
		    }
		}
		else if (cluscount[clusA] > 1) {
                    /* Can be removed from A */
                    areaface_a = area[face_a];
                    centA0 = cent[3*face_a];
                    centA1 = cent[3*face_a+1];
                    centA2 = cent[3*face_a+2];
		    /* Current energy */
                    eorig =  energy[clusA] + energy[clusB];
                    /* Energy with both items assigned to clusterB */
                    eAnA = (pow(sgamma[3*clusA] - centA0, 2) +
                            pow(sgamma[3*clusA+1] - centA1, 2) +
                            pow(sgamma[3*clusA+2] - centA2, 2)) /
			(srho[clusA] - areaface_a);
                    eBwA = (pow(sgamma[3*clusB] + centA0, 2) +
                            pow(sgamma[3*clusB+1] + centA1, 2) +
                            pow(sgamma[3*clusB+2] + centA2, 2)) /
			(srho[clusB] + areaface_a);
                    eB = eAnA + eBwA;
                    /* Compare energy contributions */
                    if (eB > eorig) {
			/* Flag clusters as modified */
                        mod2[clusA] = 1;
                        mod2[clusB] = 1;
                        nchange += 1;
			/* reassign */
                        clusters[face_a] = clusB;
                        cluscount[clusA] -= 1;
                        cluscount[clusB] += 1;
			/* Add item A to cluster A */
                        srho[clusB] += areaface_a;
                        sgamma[3*clusB] += centA0;
                        sgamma[3*clusB+1] += centA1;
                        sgamma[3*clusB+2] += centA2;
                        /* Remove item A from cluster A */
                        srho[clusA] -= areaface_a;
                        sgamma[3*clusA] -= centA0;
                        sgamma[3*clusA+1] -= centA1;
                        sgamma[3*clusA+2] -= centA2;
                        /* Update cluster energy */
                        energy[clusA] = eAnA;
                        energy[clusB] = eBwA;
		    }
		}
                else if (cluscount[clusB] > 1) {
                    /* Can be removed from B */
		    areaface_b = area[face_b];
                    centB0 = cent[3*face_b];
                    centB1 = cent[3*face_b+1];
                    centB2 = cent[3*face_b+2];
                    /* Current energy */
                    eorig =  energy[clusA] + energy[clusB];
                    /* Energy with both items assigned to cluster A */
                    eAwB = (pow(sgamma[3*clusA] + centB0, 2) +
                            pow(sgamma[3*clusA+1] + centB1, 2) +
                            pow(sgamma[3*clusA+2] + centB2, 2)) /
			(srho[clusA] + areaface_b);
                    eBnB = (pow(sgamma[3*clusB] - centB0, 2) +
                            pow(sgamma[3*clusB+1] - centB1, 2) +
                            pow(sgamma[3*clusB+2] - centB2, 2)) /
			(srho[clusB] - areaface_b);
                    eA = eAwB + eBnB;
                    /* If moving face B reduces cluster energy */
                    if (eA > eorig) {
                        mod2[clusA] = 1;
                        mod2[clusB] = 1;
                        nchange+=1;
			/* reassign */
                        clusters[face_b] = clusA;
                        cluscount[clusB] -= 1;
                        cluscount[clusA] += 1;
                        /* Update cluster A mass and centroid */
                        srho[clusA] += areaface_b;
                        sgamma[3*clusA] += centB0;
                        sgamma[3*clusA+1] += centB1;
                        sgamma[3*clusA+2] += centB2;
                        srho[clusB] -= areaface_b;
                        sgamma[3*clusB] -= centB0;
                        sgamma[3*clusB+1] -= centB1;
                        sgamma[3*clusB+2] -= centB2;
                        /* Update cluster energy */
                        energy[clusA] = eAwB;
                        energy[clusB] = eBnB;
		    }
		}
	    }
	}
	niter += 1;
    }
    free(mod1);
    free(mod2);
}


/*************************************** optimize_cluster ****/
/* Python interface function for cluster optimization */
/* args:
   int clusters (npoints)
   int neigh (npoints, maxneigh)
   int nneigh (npoints)
   float area (npoints)
   float cent (npoints, 3)
   int edges (nedges, 2)
   int npoints
   int maxneigh
   int nedges
   int nclus  : the targeted number of points
   int maxiter
*/

static int optimize_cluster(int *clusters, int *neigh, int *nneigh,
			     float *area, float *cent, int *edges,
			     int npoints, int maxneigh, int nedges,
			     int nclus, int maxiter)
{
    int iso_try=10;
    int i, j, ndisc;

    /* Allocate arrays for cluster centers, masses, and energies */
    int *cluscount = calloc(nclus, sizeof(int));
    float *sgamma = calloc(nclus*3, sizeof(float));
    float *srho = calloc(nclus, sizeof(float));
    float *energy = calloc(nclus, sizeof(float));

    init_clusters(clusters, neigh, nneigh, area, nclus, npoints, maxneigh);
    /* print_clusters("init", clusters, npoints); */

    /* Eliminate null clusters by growing existing null clusters */
    grow_null(clusters, edges, nedges);
    /* print_clusters("growinit", clusters, npoints); */

    /* Assign any remaining clusters to 0 (just in case null clusters fails) */
    for (i=0; i<npoints; ++i)
        if (clusters[i] == -1)
            clusters[i] = 0;
    /* print_clusters("just in case", clusters, npoints); */

    /* Count number of points in clusters */
    for (i=0; i<npoints; ++i)
	cluscount[clusters[i]] += 1;
    /* print_clusters("cluscount", cluscount, nclus); */

    /* Compute initial masses of clusters */
    for (i=0; i<npoints; ++i) {
	j = clusters[i];
        srho[j] += area[i];
        sgamma[3*j] += cent[3*i];
        sgamma[3*j+1] += cent[3*i+1];
        sgamma[3*j+2] += cent[3*i+2];
    }
    for (j=0; j<nclus; ++j)
        energy[j] = (pow(sgamma[3*j], 2) +
		     pow(sgamma[3*j+1], 2) +
		     pow(sgamma[3*j+2], 2)) / srho[j];

    /* print_clusters("before optimize", clusters,npoints); */

    /* Optimize clusters */
    minimize_energy(edges, clusters, area, sgamma, cent, srho, cluscount,
                    energy, nedges, nclus, maxiter);
    /* print_clusters("after optimize", clusters,npoints); */

    /* Identify isolated clusters here */
    ndisc = disconnected(clusters, neigh, nneigh, nclus, npoints, maxneigh);
    /* print("ISOLATED CLUSTERS: %d\n", ndisc); */
    /* print_clusters("after disconnected", clusters, npoints); */

    int niter = 0;
    while (ndisc && niter < iso_try) {
	/* print("====== ITERATION %d ======\n", niter); */
	grow_null(clusters, edges, nedges);
	/* print_clusters("grow_null", clusters, npoints); */

	/* Re-optimize clusters */
	minimize_energy(edges, clusters, area, sgamma, cent, srho, cluscount,
                    energy, nedges, nclus, maxiter);
	/* print_clusters("reoptimize", clusters, npoints); */

	/* Check again for disconnected clusters */
	for (i=0; i<npoints; ++i)
	    if (clusters[i] == -1)
		clusters[i] = 0;
	/* print_clusters("set_null", clusters,npoints); */

	ndisc = disconnected(clusters, neigh, nneigh, nclus, npoints, maxneigh);
	/* print("new ISOLATED CLUSTERS: %d\n", ndisc); */
	/* print_clusters("after disconnected", clusters,npoints); */
	/* goto ret1; */
        niter += 1;

        if (ndisc) {
	    grow_null(clusters, edges, nedges);

            /* Check again for disconnected clusters */
	    for (i=0; i<npoints; ++i)
		if (clusters[i] == -1)
		    clusters[i] = 0;
	}
    }
/* ret1: */
    free(cluscount);
    free(sgamma);
    free(srho);
    free(energy);

    return ndisc;
    }

/************************************************ cluster ****/
/* Python interface function for cluster optimization */
static char cluster__doc__[] = "\
\n\
Parameters\n\
----------\n\
neigh: int32 array (npoints, maxneigh)\n\
nneigh: int32 array (npoints)\n\
area: float32 array (npoints)\n\
cent: float32 array (npoints, 3)\n\
edges: int32 array (nedges, 2)\n\
nclus: int32\n\
    The targeted number of points\n\
maxiter: int32\n\
    The maximum number of iterations\n\
";

PyObject * cluster(PyObject *dummy, PyObject *args)
{
    PyObject *a1=NULL, *a2=NULL, *a3=NULL, *a4=NULL, *a5=NULL;
    PyObject *arr1=NULL, *arr2=NULL, *arr3=NULL, *arr4=NULL, *arr5=NULL;
    int *neigh, *nneigh, *edges, *clusters;
    float *area, *cent;
    int nclus, maxiter;
    int ndisc = -1;
    PyObject *ret1 = NULL;

    /* print("============= This is C cluster==============\n"); */
    if (!PyArg_ParseTuple(args, "OOOOOii", &a1, &a2, &a3, &a4, &a5,
			  &nclus, &maxiter)) return NULL;
    arr1 = PyArray_FROM_OTF(a1, NPY_INT, NPY_ARRAY_IN_ARRAY);
    if (arr1 == NULL) return NULL;
    arr2 = PyArray_FROM_OTF(a2, NPY_INT, NPY_ARRAY_IN_ARRAY);
    if (arr2 == NULL) goto fail;
    arr3 = PyArray_FROM_OTF(a3, NPY_FLOAT, NPY_ARRAY_IN_ARRAY);
    if (arr3 == NULL) goto fail;
    arr4 = PyArray_FROM_OTF(a4, NPY_FLOAT, NPY_ARRAY_IN_ARRAY);
    if (arr4 == NULL) goto fail;
    arr5 = PyArray_FROM_OTF(a5, NPY_INT, NPY_ARRAY_IN_ARRAY);
    if (arr5 == NULL) goto fail;
    /* We suppose the dimensions are correct*/
    int npoints, maxneigh, nedges;
    npy_intp *dims;
    dims = PYARRAY_DIMS(a1);
    npoints = dims[0];
    maxneigh = dims[1];
    dims = PYARRAY_DIMS(a5);
    nedges = dims[0];
    neigh = (int *)PYARRAY_DATA(arr1);
    nneigh = (int *)PYARRAY_DATA(arr2);
    area = (float *)PYARRAY_DATA(arr3);
    cent = (float *)PYARRAY_DATA(arr4);
    edges = (int *)PYARRAY_DATA(arr5);

    /* Create the return arrays */
    npy_intp dim[1];
    dim[0] = npoints;
    ret1 = PyArray_SimpleNew(1,dim, NPY_INT);
    clusters = (int *)PYARRAY_DATA(ret1);

    /* Compute */
    ndisc = optimize_cluster(clusters, neigh, nneigh,
			     area, cent, edges,
			     npoints, maxneigh, nedges,
			     nclus, maxiter);
    /* Clean up and return */
    Py_DECREF(arr1);
    Py_DECREF(arr2);
    Py_DECREF(arr3);
    Py_DECREF(arr4);
    Py_DECREF(arr5);
    return Py_BuildValue("(Oi)", ret1, ndisc);

fail:
    Py_XDECREF(arr1);
    Py_XDECREF(arr2);
    Py_XDECREF(arr3);
    Py_XDECREF(arr4);
    Py_XDECREF(arr5);
    return NULL;
}


/********************************************************/
/* The public methods defined in this module */
static PyMethodDef extension_methods[] = {
  {"cluster", cluster, METH_VARARGS, cluster__doc__},
  {NULL, NULL, 0, NULL}        /* Sentinel */
};

/* Initialize the module */
static struct PyModuleDef moduledef = {
  PyModuleDef_HEAD_INIT,
  "clust_c",   // module name
  NULL,      // module doc
  -1,        //sizeof(struct module_state),
  extension_methods,
  NULL,
  NULL, //myextension_traverse,
  NULL, //myextension_clear,
  NULL
};

PyObject *PyInit_clust_c(void)
{
  PyObject* m;
  m = PyModule_Create(&moduledef);
  if (m == NULL)
    return NULL;
  PyModule_AddStringConstant(m,"__version__",__version__);
  PyModule_AddStringConstant(m,"__doc__",__doc__);
  PyModule_AddIntConstant(m,"_accelerated",1);
  import_array(); /* Get access to numpy array API */
  return m;
}

/* End */
