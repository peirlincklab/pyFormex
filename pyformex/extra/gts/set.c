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
 * This is a modified version of the set example coming with the
 * GTS library. Copyright (C) 1999 Stéphane Popinet
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

static void write_edge (GtsSegment * s, FILE * fp)
{
  fprintf (fp, "VECT 1 2 0 2 0 %g %g %g %g %g %g\n",
	   GTS_POINT (s->v1)->x,
	   GTS_POINT (s->v1)->y,
	   GTS_POINT (s->v1)->z,
	   GTS_POINT (s->v2)->x,
	   GTS_POINT (s->v2)->y,
	   GTS_POINT (s->v2)->z);
}

/* set - compute set operations between surfaces */
int main (int argc, char * argv[])
{
  GtsSurface * s1, * s2, * s3;
  GtsSurfaceInter * si;
  GNode * tree1, * tree2;
  FILE * fptr;
  GtsFile * fp;
  int c = 0;
  gboolean verbose = FALSE;
  gboolean inter = FALSE;
  gboolean check_self_intersection = FALSE;
  gboolean binary = FALSE;
  gchar * operation, * file1, * file2;
  gboolean closed = TRUE, is_open1, is_open2;

  if (!setlocale (LC_ALL, "POSIX"))
    g_warning ("cannot set locale to POSIX");

  /* parse options using getopt */
  while (c != EOF) {
#ifdef HAVE_GETOPT_LONG
    static struct option long_options[] = {
      {"inter", no_argument, NULL, 'i'},
      {"self", no_argument, NULL, 's'},
      {"binary", no_argument, NULL, 'b'},
      {"help", no_argument, NULL, 'h'},
      {"verbose", no_argument, NULL, 'v'},
      { NULL }
    };
    int option_index = 0;
    switch ((c = getopt_long (argc, argv, "hvisb",
			      long_options, &option_index))) {
#else /* not HAVE_GETOPT_LONG */
    switch ((c = getopt (argc, argv, "hvisb"))) {
#endif /* not HAVE_GETOPT_LONG */
    case 's': /* self */
      check_self_intersection = TRUE;
      break;
    case 'i': /* inter */
      inter = TRUE;
      break;
    case 'b': /* binary */
      binary = TRUE;
      break;
    case 'v': /* verbose */
      verbose = TRUE;
      break;
    case 'h': /* help */
      fprintf (stderr,
	       "Usage: gtsset [OPTION] OPERATION surface1.gts surface2.gts\n"
	       "Compute  boolean  operations  between  surfaces.\n"
	       "OPERATION  is one of: union, inter, diff, all.\n"
	       "First three write result to stdout. 'all' writes four surface files: \n"
	       "s1out2.gts, s1in2.gts, s2out1.gts, s2in1.gts.\n"
	       "\n"
	       "  -i      --inter    output an OOGL (Geomview) representation of the curve\n"
	       "                     intersection of the surfaces\n"
	       "  -s      --self     checks that the surfaces are not self-intersecting\n"
	       "                     if one of them is, the set of self-intersecting faces\n"
	       "                     is written (as a GtsSurface) on standard output\n"
               "  -b      --binary   write the output surface to binary format\n"
               "  -v      --verbose  print statistics about the surface\n"
	       "  -h      --help     display this help and exit\n"
	       "\n"
	       "Reports bugs to %s\n",
	       "https://savannah.nongnu.org/projects/pyformex/");
      return 0; /* success */
      break;
    case '?': /* wrong options */
      fprintf (stderr, "Try `gtsset -h' for more information.\n");
      return 1; /* failure */
    }
  }

  if (optind >= argc) { /* missing OPERATION */
    fprintf (stderr,
	     "gtsset: missing OPERATION\n"
	     "Try `gtsset --help' for more information.\n");
    return 1; /* failure */
  }
  operation = argv[optind++];

  if (optind >= argc) { /* missing FILE1 */
    fprintf (stderr,
	     "gtsset: missing FILE1\n"
	     "Try `gtsset --help' for more information.\n");
    return 1; /* failure */
  }
  file1 = argv[optind++];

  if (optind >= argc) { /* missing FILE2 */
    fprintf (stderr,
	     "gtsset: missing FILE2\n"
	     "Try `gtsset --help' for more information.\n");
    return 1; /* failure */
  }
  file2 = argv[optind++];

  /* open first file */
  if ((fptr = fopen (file1, "rt")) == NULL) {
    fprintf (stderr, "gtsset: can not open file `%s'\n", file1);
    return 1;
  }
  /* reads in first surface file */
  s1 = GTS_SURFACE (gts_object_new (GTS_OBJECT_CLASS (gts_surface_class ())));
  fp = gts_file_new (fptr);
  if (gts_surface_read (s1, fp)) {
    fprintf (stderr, "gtsset: `%s' is not a valid GTS surface file\n",
	     file1);
    fprintf (stderr, "%s:%d:%d: %s\n", file1, fp->line, fp->pos, fp->error);
    return 1;
  }
  gts_file_destroy (fp);
  fclose (fptr);

  /* open second file */
  if ((fptr = fopen (file2, "rt")) == NULL) {
    fprintf (stderr, "gtsset: can not open file `%s'\n", file2);
    return 1;
  }
  /* reads in second surface file */
  s2 = GTS_SURFACE (gts_object_new (GTS_OBJECT_CLASS (gts_surface_class ())));
  fp = gts_file_new (fptr);
  if (gts_surface_read (s2, fp)) {
    fprintf (stderr, "gtsset: `%s' is not a valid GTS surface file\n",
	     file2);
    fprintf (stderr, "%s:%d:%d: %s\n", file2, fp->line, fp->pos, fp->error);
    return 1;
  }
  gts_file_destroy (fp);
  fclose (fptr);

  /* display summary information about both surfaces */
  if (verbose) {
    gts_surface_print_stats (s1, stderr);
    gts_surface_print_stats (s2, stderr);
  }

  /* check that the surfaces are orientable manifolds */
  if (!gts_surface_is_orientable (s1)) {
    fprintf (stderr, "gtsset: surface `%s' is not an orientable manifold\n",
	     file1);
    return 1;
  }
  if (!gts_surface_is_orientable (s2)) {
    fprintf (stderr, "gtsset: surface `%s' is not an orientable manifold\n",
	     file2);
    return 1;
  }

  /* check that the surfaces are not self-intersecting */
  if (check_self_intersection) {
    GtsSurface * self_intersects;

    self_intersects = gts_surface_is_self_intersecting (s1);
    if (self_intersects != NULL) {
      fprintf (stderr, "gtsset: surface `%s' is self-intersecting\n", file1);
      if (verbose)
	gts_surface_print_stats (self_intersects, stderr);
      gts_surface_write (self_intersects, stdout);
      gts_object_destroy (GTS_OBJECT (self_intersects));
      return 1;
    }
    self_intersects = gts_surface_is_self_intersecting (s2);
    if (self_intersects != NULL) {
      fprintf (stderr, "gtsset: surface `%s' is self-intersecting\n", file2);
      if (verbose)
	gts_surface_print_stats (self_intersects, stderr);
      gts_surface_write (self_intersects, stdout);
      gts_object_destroy (GTS_OBJECT (self_intersects));
      return 1;
    }
  }

  /* build bounding box tree for first surface */
  tree1 = gts_bb_tree_surface (s1);
  is_open1 = gts_surface_volume (s1) < 0. ? TRUE : FALSE;

  /* build bounding box tree for second surface */
  tree2 = gts_bb_tree_surface (s2);
  is_open2 = gts_surface_volume (s2) < 0. ? TRUE : FALSE;

  si = gts_surface_inter_new (gts_surface_inter_class (),
			      s1, s2, tree1, tree2, is_open1, is_open2);
  g_assert (gts_surface_inter_check (si, &closed));
  if (!closed) {
    fprintf (stderr,
	     "gtsset: the intersection of `%s' and `%s' is not a closed curve\n",
	     file1, file2);
    return 1;
  }

  s3 = gts_surface_new (gts_surface_class (),
			gts_face_class (),
			gts_edge_class (),
			gts_vertex_class ());
  if (!strcmp (operation, "union")) {
    gts_surface_inter_boolean (si, s3, GTS_1_OUT_2);
    gts_surface_inter_boolean (si, s3, GTS_2_OUT_1);
  }
  else if (!strcmp (operation, "inter")) {
    gts_surface_inter_boolean (si, s3, GTS_1_IN_2);
    gts_surface_inter_boolean (si, s3, GTS_2_IN_1);
  }
  else if (!strcmp (operation, "diff")) {
    gts_surface_inter_boolean (si, s3, GTS_1_OUT_2);
    gts_surface_inter_boolean (si, s3, GTS_2_IN_1);
    gts_surface_foreach_face (si->s2, (GtsFunc) gts_triangle_revert, NULL);
    gts_surface_foreach_face (s2, (GtsFunc) gts_triangle_revert, NULL);
  }
  else if (!strcmp (operation, "all")) {
    GtsSurface * s1out2, * s1in2, * s2out1, * s2in1;
    FILE * fp;

    s1out2 = gts_surface_new (gts_surface_class (),
			      gts_face_class (),
			      gts_edge_class (),
			      gts_vertex_class ());
    s1in2 = gts_surface_new (gts_surface_class (),
			     gts_face_class (),
			     gts_edge_class (),
			     gts_vertex_class ());
    s2out1 = gts_surface_new (gts_surface_class (),
			      gts_face_class (),
			      gts_edge_class (),
			      gts_vertex_class ());
    s2in1 = gts_surface_new (gts_surface_class (),
			     gts_face_class (),
			     gts_edge_class (),
			     gts_vertex_class ());
    gts_surface_inter_boolean (si, s1out2, GTS_1_OUT_2);
    gts_surface_inter_boolean (si, s1in2, GTS_1_IN_2);
    gts_surface_inter_boolean (si, s2out1, GTS_2_OUT_1);
    gts_surface_inter_boolean (si, s2in1, GTS_2_IN_1);
    fp = fopen ("s1out2.gts", "w");
    gts_surface_write (s1out2, fp);
    fclose (fp);
    fp = fopen ("s1in2.gts", "w");
    gts_surface_write (s1in2, fp);
    fclose (fp);
    fp = fopen ("s2out1.gts", "w");
    gts_surface_write (s2out1, fp);
    fclose (fp);
    fp = fopen ("s2in1.gts", "w");
    gts_surface_write (s2in1, fp);
    fclose (fp);
    gts_object_destroy (GTS_OBJECT (s1out2));
    gts_object_destroy (GTS_OBJECT (s1in2));
    gts_object_destroy (GTS_OBJECT (s2out1));
    gts_object_destroy (GTS_OBJECT (s2in1));
  }
  else {
    fprintf (stderr,
	     "gtsset: operation `%s' unknown\n"
	     "Try `gtsset --help' for more information.\n",
	     operation);
    return 1;
  }

  /* check that the resulting surface is not self-intersecting */
  if (check_self_intersection) {
    GtsSurface * self_intersects;

    self_intersects = gts_surface_is_self_intersecting (s3);
    if (self_intersects != NULL) {
      fprintf (stderr, "gtsset: the resulting surface is self-intersecting\n");
      if (verbose)
	gts_surface_print_stats (self_intersects, stderr);
      gts_surface_write (self_intersects, stdout);
      gts_object_destroy (GTS_OBJECT (self_intersects));
      return 1;
    }
  }
  /* display summary information about the resulting surface */
  if (verbose)
    gts_surface_print_stats (s3, stderr);
  /* write resulting surface to standard output */
  if (inter) {
    printf ("LIST {\n");
    g_slist_foreach (si->edges, (GFunc) write_edge, stdout);
    printf ("}\n");
  }
  else {
    GTS_POINT_CLASS (gts_vertex_class ())->binary = binary;
    gts_surface_write (s3, stdout);
  }

  /* destroy surfaces */
  gts_object_destroy (GTS_OBJECT (s1));
  gts_object_destroy (GTS_OBJECT (s2));
  gts_object_destroy (GTS_OBJECT (s3));
  gts_object_destroy (GTS_OBJECT (si));

  /* destroy bounding box trees (including bounding boxes) */
  gts_bb_tree_destroy (tree1, TRUE);
  gts_bb_tree_destroy (tree2, TRUE);

  return 0;
}
