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
 * This is a modified version of the refine example coming with the
 * GTS library. Copyright (C) 1999 Stéphane Popinet
 */

#include <stdlib.h>
#include <locale.h>
#include <math.h>
#include "config.h"
#ifdef HAVE_GETOPT_H
#  include <getopt.h>
#endif /* HAVE_GETOPT_H */
#ifdef HAVE_UNISTD_H
#  include <unistd.h>
#endif /* HAVE_UNISTD_H */
#include "gts.h"

#ifndef PI
#define PI 3.14159265359
#endif

typedef enum { NUMBER, COST } StopOptions;

static gboolean stop_number_verbose (gdouble cost, guint number, guint * max)
{
  static guint nmax = 0, nold = 0;
  static GTimer * timer = NULL, * total_timer = NULL;

  g_return_val_if_fail (max != NULL, TRUE);

  if (timer == NULL) {
    nmax = nold = number;
    timer = g_timer_new ();
    total_timer = g_timer_new ();
    g_timer_start (total_timer);
  }

  if (number != nold && number % 1211 == 0 &&
      number > nmax && nmax < *max) {
    gdouble total_elapsed = g_timer_elapsed (total_timer, NULL);
    gdouble remaining;
    gdouble hours, mins, secs;
    gdouble hours1, mins1, secs1;

    g_timer_stop (timer);

    hours = floor (total_elapsed/3600.);
    mins = floor ((total_elapsed - 3600.*hours)/60.);
    secs = floor (total_elapsed - 3600.*hours - 60.*mins);

    remaining = total_elapsed*((*max - nmax)/(gdouble) (number - nmax) - 1.);
    hours1 = floor (remaining/3600.);
    mins1 = floor ((remaining - 3600.*hours1)/60.);
    secs1 = floor (remaining - 3600.*hours1 - 60.*mins1);

    fprintf (stderr,
	     "\rEdges: %10u %3.0f%% %6.0f edges/s "
	     "Elapsed: %02.0f:%02.0f:%02.0f "
	     "Remaining: %02.0f:%02.0f:%02.0f ",
	     number,
	     100.*(number - nmax)/(*max - nmax),
	     (number - nold)/g_timer_elapsed (timer, NULL),
	     hours, mins, secs,
	     hours1, mins1, secs1);
    fflush (stderr);

    nold = number;
    g_timer_start (timer);
  }
  if (number > *max) {
    g_timer_destroy (timer);
    g_timer_destroy (total_timer);
    return TRUE;
  }
  return FALSE;
}

static gboolean stop_number (gdouble cost, guint number, guint * max)
{
  if (number > *max)
    return TRUE;
  return FALSE;
}

static gboolean stop_cost_verbose (gdouble cost, guint number, gdouble * min)
{
  g_return_val_if_fail (min != NULL, TRUE);

  if (number % 511 == 0) {
    fprintf (stderr, "\rEdges: %10u Cost: %10g ", number, cost);
    fflush (stderr);
  }
  if (cost < *min)
    return TRUE;
  return FALSE;
}

static gboolean stop_cost (gdouble cost, guint number, gdouble * min)
{
  if (cost < *min)
    return TRUE;
  return FALSE;
}

static gboolean stop_log_cost (gdouble cost, guint number)
{
  fprintf (stderr, "%d %g\n", number, cost);
  return FALSE;
}

/* refine - produce a refined version of the input */
int main (int argc, char * argv[])
{
  GtsSurface * s;
  gboolean verbose = FALSE;
  gboolean log_cost = FALSE;
  guint number = 0;
  gdouble cmin = 0.0;
  StopOptions stop = NUMBER;
  GtsKeyFunc refine_func = NULL;
  GtsStopFunc stop_func = NULL;
  gpointer stop_data = NULL;
  int c = 0;
  GtsFile * fp;

  if (!setlocale (LC_ALL, "POSIX"))
    g_warning ("cannot set locale to POSIX");

  /* parse options using getopt */
  while (c != EOF) {
#ifdef HAVE_GETOPT_LONG
    static struct option long_options[] = {
      {"help", no_argument, NULL, 'h'},
      {"verbose", no_argument, NULL, 'v'},
      {"number", required_argument, NULL, 'n'},
      {"cost", required_argument, NULL, 'c'},
      {"log", no_argument, NULL, 'L'},
      { NULL }
    };
    int option_index = 0;
    switch ((c = getopt_long (argc, argv, "hvc:n:L",
			      long_options, &option_index))) {
#else /* not HAVE_GETOPT_LONG */
    switch ((c = getopt (argc, argv, "hvc:n:L"))) {
#endif /* not HAVE_GETOPT_LONG */
    case 'L': /* log */
      log_cost = TRUE;
      break;
    case 'n': /* stop by number */
      stop = NUMBER;
      number = atoi (optarg);
      break;
    case 'c': /* stop by cost */
      stop = COST;
      cmin = atof (optarg);
      break;
    case 'v': /* verbose */
      verbose = TRUE;
      break;
    case 'h': /* help */
      fprintf (stderr,
             "Usage: gtsrefine [OPTION] < file.gts\n"
	     "Construct a refined version of the input.\n"
	     "\n"
	     "  -n N, --number=N    stop the refining process if the number of\n"
	     "                      edges was to be greater than N\n"
	     "  -c C, --cost=C      stop the refining process if the cost of refining\n"
	     "                      an edge is smaller than C\n"
	     "  -L    --log         logs the evolution of the cost\n"
	     "  -v    --verbose     print statistics about the surface\n"
	     "  -h    --help        display this help and exit\n"
	     "\n"
	     "Report bugs to %s\n",
	     "https://savannah.nongnu.org/projects/pyformex/");
      return 0; /* success */
      break;
    case '?': /* wrong options */
      fprintf (stderr, "Try `gtsrefine -h' for more information.\n");
      return 1; /* failure */
    }
  }

  /* read surface in */
  s = gts_surface_new (gts_surface_class (),
		       gts_face_class (),
		       gts_edge_class (),
		       gts_vertex_class ());
  fp = gts_file_new (stdin);
  if (gts_surface_read (s, fp)) {
    fputs ("gtsrefine: the file on standard input is not a valid GTS file\n",
	   stderr);
    fprintf (stderr, "stdin:%d:%d: %s\n", fp->line, fp->pos, fp->error);
    return 1; /* failure */
  }

  /* if verbose on print stats */
  if (verbose) {
    gts_surface_print_stats (s, stderr);
    fprintf (stderr, "# volume: %g area: %g\n",
	     gts_surface_volume (s), gts_surface_area (s));
  }

  /* select the right refining process */
  if (log_cost)
    stop_func = (GtsStopFunc) stop_log_cost;
  else {
    switch (stop) {
    case NUMBER:
      if (verbose)
	stop_func = (GtsStopFunc) stop_number_verbose;
      else
	stop_func = (GtsStopFunc) stop_number;
      stop_data = &number;
      break;
    case COST:
      if (verbose)
	stop_func = (GtsStopFunc) stop_cost_verbose;
      else
	stop_func = (GtsStopFunc) stop_cost;
      stop_data = &cmin;
      break;
    default:
      g_assert_not_reached ();
    }
  }

  gts_surface_refine (s,
		      refine_func, NULL,
		      NULL, NULL,
		      stop_func, stop_data);

  /* if verbose on print stats */
  if (verbose) {
    fputc ('\n', stderr);
    gts_surface_print_stats (s, stderr);
    fprintf (stderr, "# volume: %g area: %g\n",
	     gts_surface_volume (s), gts_surface_area (s));
  }

  /* write resulting surface to standard output */
  gts_surface_write (s, stdout);

  return 0; /* success */
}
