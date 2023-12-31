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
 * This is a modified version of the smooth example coming with the
 * GTS library. Copyright (C) 1999 Stéphane Popinet
 */

#include <stdio.h>
#include <locale.h>
#include <stdlib.h>
#include <math.h>
#include "config.h"
#ifdef HAVE_GETOPT_H
#  include <getopt.h>
#endif /* HAVE_GETOPT_H */
#ifdef HAVE_UNISTD_H
#  include <unistd.h>
#endif /* HAVE_UNISTD_H */
#include "gts.h"

static void smooth_vertex (GtsVertex * v, gpointer * data)
{
  GtsSurface * s = data[0];

  if (!gts_vertex_is_boundary (v, s)) {
    gdouble * lambda = data[1];
    GSList * vertices = gts_vertex_neighbors (v, NULL, s);
    GSList * i;
    GtsVector U0 = { 0., 0., 0.};
    guint n = 0;

    i = vertices;
    while (i) {
      GtsPoint * p = i->data;
      U0[0] += p->x;
      U0[1] += p->y;
      U0[2] += p->z;
      n++;
      i = i->next;
    }
    g_slist_free (vertices);

    if (n > 0) {
      GTS_POINT (v)->x += (*lambda)*(U0[0]/n - GTS_POINT (v)->x);
      GTS_POINT (v)->y += (*lambda)*(U0[1]/n - GTS_POINT (v)->y);
      GTS_POINT (v)->z += (*lambda)*(U0[2]/n - GTS_POINT (v)->z);
    }
  }
}

static void smooth_fold (GtsVertex * v, gpointer * data)
{
  gdouble * maxcosine2 = data[2];
  GSList * i = v->segments;
  gboolean folded = FALSE;
  guint * nfold = data[3];

  while (i && !folded) {
    if (GTS_IS_EDGE (i->data)) {
      GtsEdge * e = i->data;

      if (gts_triangles_are_folded (e->triangles,
				    GTS_SEGMENT (e)->v1,
				    GTS_SEGMENT (e)->v2,
				    *maxcosine2))
	folded = TRUE;
    }
    i = i->next;
  }
  if (folded) {
    (*nfold)++;
    smooth_vertex (v, data);
  }
}

int main (int argc, char * argv[])
{
  GtsSurface * s;
  GtsFile * fp;
  int c = 0;
  gboolean verbose = FALSE;
  guint n, niter;
  gdouble lambda;
  gpointer data[4];
  gboolean fold = FALSE;
  gdouble maxcosine2 = 0.;
  guint nfold = 1;

  if (!setlocale (LC_ALL, "POSIX"))
    g_warning ("cannot set locale to POSIX");

  /* parse options using getopt */
  while (c != EOF) {
#ifdef HAVE_GETOPT_LONG
    static struct option long_options[] = {
      {"fold", required_argument, NULL, 'f'},
      {"help", no_argument, NULL, 'h'},
      {"verbose", no_argument, NULL, 'v'},
      { NULL }
    };
    int option_index = 0;
    switch ((c = getopt_long (argc, argv, "hvf:",
			      long_options, &option_index))) {
#else /* not HAVE_GETOPT_LONG */
    switch ((c = getopt (argc, argv, "hvf:"))) {
#endif /* not HAVE_GETOPT_LONG */
    case 'f': /* fold */
      fold = TRUE;
      maxcosine2 = cos (atof (optarg)*3.14159265359/180.);
      maxcosine2 *= maxcosine2;
      break;
    case 'v': /* verbose */
      verbose = TRUE;
      break;
    case 'h': /* help */
      fprintf (stderr,
             "Usage: gtssmooth [OPTION] LAMBDA NITER < file.gts > smooth.gts\n"
	     "Smooth a GTS file by applying NITER iterations of a Laplacian filter\n"
	     "of parameter LAMBDA.\n"
	     "\n"
	     "  -f VAL  --fold=VAL   smooth only folds\n"
	     "  -v      --verbose    print statistics about the surface\n"
	     "  -h      --help       display this help and exit\n"
	     "\n"
	     "Reports bugs to %s\n",
	     "https://savannah.nongnu.org/projects/pyformex/");
      return 0; /* success */
      break;
    case '?': /* wrong options */
      fprintf (stderr, "Try `gtssmooth -h' for more information.\n");
      return 1; /* failure */
    }
  }

  if (optind >= argc) { /* missing lambda */
    fprintf (stderr,
	     "gtssmooth: missing LAMBDA\n"
	     "Try `gtssmooth --help' for more information.\n");
    return 1; /* failure */
  }
  lambda = atof (argv[optind++]);

  if (optind >= argc) { /* missing niter */
    fprintf (stderr,
	     "gtssmooth: missing NITER\n"
	     "Try `gtssmooth --help' for more information.\n");
    return 1; /* failure */
  }
  niter = atoi (argv[optind++]);

  s = gts_surface_new (gts_surface_class (),
		       gts_face_class (),
		       gts_edge_class (),
		       gts_vertex_class ());
  fp = gts_file_new (stdin);
  if (gts_surface_read (s, fp)) {
    fputs ("gtssmooth: file on standard input is not a valid GTS file\n",
	   stderr);
    fprintf (stderr, "stdin:%d:%d: %s\n", fp->line, fp->pos, fp->error);
    return 1; /* failure */
  }

  if (verbose)
    gts_surface_print_stats (s, stderr);

  data[0] = s;
  data[1] = &lambda;
  data[2] = &maxcosine2;
  data[3] = &nfold;

  for (n = 1; n <= niter && (!fold || nfold > 0); n++) {
    if (fold) {
      nfold = 0;
      gts_surface_foreach_vertex (s, (GtsFunc) smooth_fold, data);
    }
    else
      gts_surface_foreach_vertex (s, (GtsFunc) smooth_vertex, data);
    if (verbose)
      fprintf (stderr, "\rIteration: %10u %3.0f%% ",
	       n,
	       100.*n/niter);
  }

  if (verbose) {
    fputc ('\n', stderr);
    gts_surface_print_stats (s, stderr);
  }

  gts_surface_write (s, stdout);

  return 0;
}
