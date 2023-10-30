//
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

/*
 *
 * Determine whether points are inside a given closed surface or not.
 *
 */

#include <stdlib.h>
#include <locale.h>
#include <string.h>
#include "config.h"
#ifdef HAVE_GETOPT_H
#  include <getopt.h>
#endif /* HAVE_GETOPT_H */
#ifdef HAVE_UNISTD_H
#  include <unistd.h>
#endif /* HAVE_UNISTD_H */
#include "gts.h"

#include <math.h>

static gboolean ray_intersects_triangle (GtsPoint * D, GtsPoint * E,
					 GtsTriangle * t)
{
  GtsPoint * A, * B, * C;
  gint ABCE, ABCD, ADCE, ABDE, BCDE;

  gts_triangle_vertices (t, (GtsVertex **) &A,
			 (GtsVertex **) &B,
			 (GtsVertex **) &C);

  ABCE = gts_point_orientation_3d_sos (A, B, C, E);
  ABCD = gts_point_orientation_3d_sos (A, B, C, D);
  if (ABCE < 0 || ABCD > 0) {
    GtsPoint * tmpp;
    gint tmp;

    tmpp = E; E = D; D = tmpp;
    tmp = ABCE; ABCE = ABCD; ABCD = tmp;
  }
  if (ABCE < 0 || ABCD > 0)
    return FALSE;
  ADCE = gts_point_orientation_3d_sos (A, D, C, E);
  if (ADCE < 0)
    return FALSE;
  ABDE = gts_point_orientation_3d_sos (A, B, D, E);
  if (ABDE < 0)
    return FALSE;
  BCDE = gts_point_orientation_3d_sos (B, C, D, E);
  if (BCDE < 0)
    return FALSE;
  return TRUE;
}

/*
 * gts_point_is_inside_surface:
 * @p: a #GtsPoint.
 * @tree: a bounding box tree of the faces of a closed, orientable
 * surface (see gts_bb_tree_surface()).
 * @is_open: %TRUE if the surface defined by @tree is "open" i.e. its volume
 * is negative, %FALSE otherwise.
 *
 * Returns: %TRUE if @p is inside the surface defined by @tree, %FALSE
 * otherwise.
 */
gboolean gts_point_is_inside_surface (GtsPoint * p,
				      GNode * tree,
				      gboolean is_open)
{
  GSList * list, * i;
  guint nc = 0;
  GtsPoint * p1;
  GtsBBox * bb;

  g_return_val_if_fail (p != NULL, FALSE);
  g_return_val_if_fail (tree != NULL, FALSE);

  bb = tree->data;
  /* BV added 0.1 in the following statement. Iin cases where bb->x2 equals 0.0,
   * the added relative tolerance fabs (bb->x2)/10 wasn't adding anything.
   * p is the point being tested. rays always shoot in positive x-direction.
   * p1 is the 'endpoint' of the ray. It should be outside of the bb, as
   * the ray goes in principle to infinity.
   */
  p1 = gts_point_new (gts_point_class (), bb->x2 + fabs (bb->x2)/10. + 0.1, p->y, p->z);
#ifdef DEBUG
  fprintf(stderr,"NEW POINT %f %f %f\n", p1->x, p1->y, p1->z);
#endif
  i = list = gts_bb_tree_stabbed (tree, p);
  while (i) {
    GtsTriangle * t = GTS_TRIANGLE (GTS_BBOX (i->data)->bounded);
#ifdef DEBUG
    fprintf(stderr,"Shooting...\n");
#endif
    if (ray_intersects_triangle (p, p1, t)){
#ifdef DEBUG
        fprintf(stderr,"...hit!\n");
#endif
      nc++;
    }
    i = i->next;
  }
  g_slist_free (list);
  gts_object_destroy (GTS_OBJECT (p1));

  return is_open ? (nc % 2 == 0) : (nc % 2 != 0);
}

/* inside - check if points are inside a surface */
int main (int argc, char * argv[])
{
  GtsSurface * s1;
  GNode * tree1;
  GtsPoint P;
  FILE * fptr, * bbptr;
  GtsFile * fp;
  int c = 0, cnt = 0;
  double x,y,z;
  gboolean verbose = FALSE;
  gchar * file1, * file2;
  gboolean is_open1, is_inside;

  if (!setlocale (LC_ALL, "POSIX"))
    g_warning ("cannot set locale to POSIX");

  /* parse options using getopt */
  while (c != EOF) {
#ifdef HAVE_GETOPT_LONG
    static struct option long_options[] = {
      {"help", no_argument, NULL, 'h'},
      {"verbose", no_argument, NULL, 'v'}
    };
    int option_index = 0;
    switch ((c = getopt_long (argc, argv, "shv",
			      long_options, &option_index))) {
#else /* not HAVE_GETOPT_LONG */
    switch ((c = getopt (argc, argv, "shv"))) {
#endif /* not HAVE_GETOPT_LONG */
    case 'v': /* verbose */
      verbose = TRUE;
      break;
    case 'h': /* help */
      fprintf (stderr,
	"Usage: gtsinside [OPTION] FILE1 FILE2\n"
	"Test whether points are inside a closed surface.\n"
	"FILE1 is a surface file. FILE2 is a text file where each line\n"
	"contains the three coordinates of a point, separated with blanks.\n"
	"\n"
	"  -v      --verbose  print statistics about the surface\n"
	"  -h      --help     display this help and exit\n"
	"\n"
	"Reports bugs to %s\n",
	"https://savannah.nongnu.org/projects/pyformex/");
      return 0; /* success */
      break;
    case '?': /* wrong options */
      fprintf (stderr, "Try `gtsinside -h' for more information.\n");
      return 1; /* failure */
    }
  }

  if (optind >= argc) { /* missing FILE1 */
    fprintf (stderr,
	     "gtsinside: missing FILE1\n"
	     "Try `inside --help' for more information.\n");
    return 1; /* failure */
  }
  file1 = argv[optind++];

  if (optind >= argc) { /* missing FILE2 */
    fprintf (stderr,
	     "gtsinside: missing FILE2\n"
	     "Try `gtsinside --help' for more information.\n");
    return 1; /* failure */
  }
  file2 = argv[optind++];

  /* open first file */
  if ((fptr = fopen (file1, "rt")) == NULL) {
    fprintf (stderr, "gtsinside: can not open file `%s'\n", file1);
    return 1;
  }
  /* reads in first surface file */
  s1 = GTS_SURFACE (gts_object_new (GTS_OBJECT_CLASS (gts_surface_class ())));
  fp = gts_file_new (fptr);
  if (gts_surface_read (s1, fp)) {
    fprintf (stderr, "gtsinside: `%s' is not a valid GTS surface file\n",
	     file1);
    fprintf (stderr, "%s:%d:%d: %s\n", file1, fp->line, fp->pos, fp->error);
    return 1;
  }
  gts_file_destroy (fp);
  fclose (fptr);

  /* open second file */
  if ((fptr = fopen (file2, "rt")) == NULL) {
    fprintf (stderr, "gtsinside: can not open file `%s'\n", file2);
    return 1;
  }

  /* display summary information about the surface */
  if (verbose) {
    gts_surface_print_stats (s1, stderr);
  }

  /* check that the surface is an orientable manifold */
  if (!gts_surface_is_orientable (s1)) {
    fprintf (stderr, "gtsinside: surface `%s' is not an orientable manifold\n",
  	     file1);
    return 1;
  }

  /* build bounding box tree for the surface */
  tree1 = gts_bb_tree_surface (s1);
  is_open1 = gts_surface_volume (s1) < 0. ? TRUE : FALSE;
#ifdef DEBUG
  fprintf(stderr,"is_open1: %d\n",is_open1);
#endif

  /* write the bboxtree */
  if ((bbptr = fopen ("bbtree.oogl", "w")) == NULL) {
    fprintf (stderr, "gtsinside: can not open bbtree file \n");
    return 1;
  }
  gts_bb_tree_draw(tree1, 3, bbptr);
  fclose(bbptr);

  /* scan file 2 for points and determine if they are inside surface */
  while ( fscanf(fptr, "%lg %lg %lg", &x, &y, &z) == 3 ) {
    P.x = x; P.y = y; P.z = z;
    is_inside = gts_point_is_inside_surface(&P,tree1,is_open1);
#ifdef DEBUG
    fprintf(stderr,"Point %d is_inside: %d\n",cnt, is_inside);
#endif
    if (is_inside) {
	printf("%d\n",cnt);
#ifdef DEBUG
	fprintf(stderr,"YES inside!\n");
#endif
    }
#ifdef DEBUG
    fprintf(stderr,"Point %d: %lf, %lf, %lf: %d\n",cnt,P.x,P.y,P.z,is_inside);
#endif
    cnt++;
  }
  if ( !feof(fptr) ) {
    fprintf (stderr, "gtsinside: error while reading points from file `%s'\n",
  	     file2);
    return 1;
  }
  fclose (fptr);

  /* destroy surface */
  gts_object_destroy (GTS_OBJECT (s1));

  /* destroy bounding box tree (including bounding boxes) */
  gts_bb_tree_destroy (tree1, TRUE);

  return 0;
}
