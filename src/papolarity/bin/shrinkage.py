import argparse
import numpy as np
from ..gzip_utils import open_for_write
from ..tsv_reader import each_in_tsv

def sliding_row_with_window(arr, size):
    for idx in range(0, size // 2):
        yield (arr[idx], arr[0:size])
    for idx in range(size // 2, len(arr) - size // 2):
        yield (arr[idx], arr[(idx - size // 2):(idx - size // 2 + size)])
    for idx in range(len(arr) - size // 2, len(arr)):
        yield (arr[idx], arr[-size:])

# stddev --> 1
def standardize_stddev(val, val_mean, val_stddev):
    return val_mean + (val - val_mean) / val_stddev

# mean --> 0
def standardize_mean(val, val_mean, val_stddev):
    return val - val_mean

# mean --> 0
# stddev --> 1
# (aka z-score)
def standardize_mean_stddev(val, val_mean, val_stddev):
    return (val - val_mean) / val_stddev

def configure_argparser(argparser=None):
    if not argparser:
        argparser = argparse.ArgumentParser(prog="shrinkage", description = "Make length-dependend shrinkage of properties")
    argparser.add_argument('table', metavar='table.tsv', help='Table in tab-separated format')
    argparser.add_argument('sorting_field', help='Field to sort a table')
    argparser.add_argument('--fields', nargs='*', dest='fields_to_correct', default=[], help='List of fields to correct')
    argparser.add_argument('--prefix', default='shrinked_', help='Prefix for corrected column name')
    argparser.add_argument('--window', metavar='SIZE', dest='window_size', type=int, default=100, help='Size of sliding window (default: %(default)s)')
    argparser.add_argument('--mode', default='zero_mean+unit_stddev', help='Which statistics to standardize (options: zero_mean, unit_stddev, zero_mean+unit_stddev)')
    argparser.add_argument('--output-file', '-o', dest='output_file', help="Store results at this path")
    return argparser

def main():
    argparser = configure_argparser(argparser)
    args = argparser.parse_args()
    invoke(args)

def invoke(args):
    if args.mode == 'zero_mean':
        standardization = standardize_mean
    elif args.mode in ['unit_stddev', 'unit_stdev', 'unit_std']:
        standardization = standardize_stddev
    elif args.mode in ['zero_mean+unit_stddev', 'zero_mean+unit_stdev', 'zero_mean+unit_std']:
        standardization = standardize_mean_stddev
    else:
        raise ValueError(f'Unknown mode `{mode}`')

    dtype = float
    data = list(each_in_tsv(args.table))

    fields = list(data[0].keys())
    for field in [args.sorting_field, *args.fields_to_correct]:
        for row in data:
            row[field] = dtype(row[field])
    data.sort(key=lambda info: info[args.sorting_field])

    output_fields = fields[:]
    for field in args.fields_to_correct:
        output_fields.append(f'{args.prefix}{field}')

    with open_for_write(args.output_file) as output_stream:
        print('\t'.join(output_fields), file=output_stream)
        for row, window in sliding_row_with_window(data, args.window_size):
            modified_row = dict(row)
            for field in args.fields_to_correct:
                field_vals = [window_row[field] for window_row in window]
                modified_row[f'{args.prefix}{field}'] = standardization(row[field], val_mean=np.mean(field_vals), val_stddev=np.std(field_vals))
            print('\t'.join([str(modified_row[field]) for field in output_fields]), file=output_stream)
