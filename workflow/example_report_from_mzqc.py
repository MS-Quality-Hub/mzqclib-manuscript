#!/usr/local/bin/python
from mzqc import MZQCFile as qc
import logging
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import pandas as pd
import click

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

logger = logging.getLogger('simple_example')
logger.setLevel(logging.DEBUG)

def print_help():
    """
    Print the help of the tool
    :return:
    """
    ctx = click.get_current_context()
    click.echo(ctx.get_help())
    ctx.exit()

report_tmplt = """<!DOCTYPE html>
<html>
<head>
  <title>QC Report for {name}</title>
</head>
<body>

<h1>QC Report for {name}</h1>
<table>
<tr>
  <td><h2>Acquisition</h2></td>
  <td><p><img align="left" src="data:image/png;base64, {mz_plot}", width="300"></p></td>
  <td><p><img align="right" src="data:image/png;base64, {rt_plot}", width="600"></p></td>
</tr>
<tr>
  <td><h2>Calibration</h2></td>
  <td><p><img align="left" src="data:image/png;base64, {tic_plot}", width="400"></p></td>
  <td><p><img align="right" src="data:image/png;base64, {irt_plot}", width="400"></p></td>
</tr>
</table>
<h2>Contamination</h2>
{conta_tab}

</body>
</html>
"""

def plot_range_mz(mzrange):
    f, ax = plt.subplots(1)
    f.set_figwidth(1)
    ax.plot([0]*len(mzrange), mzrange, linewidth = '5')  # thicker linewidths results in inaccurate line breadth
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    ax.get_xaxis().set_visible(False)
    ax.set_frame_on(False)
    # ax.axis("tight")  # this undoes limits etc

    offset=70  # offset in px?!

    plt.ylabel("m/z", size=12)
    plt.title("MS instrument \nacquisition range \nin mass-over-charge", size=18, fontweight='bold')
    for mz_lim in mzrange:
        # ax.text(rt_lim, .03, format(rt_lim, '.2f'), size=16, horizontalalignment='center')
        ax.annotate(format(mz_lim, '.2f'), 
                    xy=(0,mz_lim),
                    horizontalalignment='center', verticalalignment='center', size=16,
                    # bbox=bbox, 
                    # arrowprops=dict(facecolor='black', shrink=0.05),
                    arrowprops=dict(facecolor='black'),
                    xytext=(offset,0), 
                    textcoords='offset pixels',
                    )
    return f

def plot_range_rt(rtrange):
    f, ax = plt.subplots(1)
    f.set_figheight(1)
    ax.plot(rtrange,[0]*len(rtrange), linewidth = '5')  # thicker linewidths results in inaccurate line breadth
    ax.set_xlim((0,round(max(rtrange)+100, -2)))
    ax.set_ylim(bottom=0)

    ax.get_yaxis().set_visible(False)
    ax.set_frame_on(False)
    # ax.axis("tight")  # this undoes limits etc

    bbox = dict(boxstyle="round", fc="0.8")
    arrowprops = dict(
        arrowstyle="->",
        connectionstyle="angle,angleA=0,angleB=90,rad=10")

    plt.xlabel("RT [s]", size=12)
    plt.title("MS instrument acquisition range over run time", size=18, fontweight='bold')

    offset=30  # offset in px?!
    for rt_lim in rtrange:
        # ax.text(rt_lim, .03, format(rt_lim, '.2f'), size=16, horizontalalignment='center')
        ax.annotate(format(rt_lim, '.2f'), 
                xy=(rt_lim, 0),
                horizontalalignment='center', size=16,
                # bbox=bbox, 
                # arrowprops=dict(facecolor='black', shrink=0.05),
                arrowprops=dict(facecolor='black'),
                xytext=(0, offset), 
                textcoords='offset pixels',
                )
    return f

def plot_to_b64(fig: plt.figure):
    figIObytes = BytesIO()
    #  https://stackoverflow.com/a/7906795/3319796
    # png needs dpi sync, jpg also bbox_inches
    fig.savefig(figIObytes, format='png', dpi=fig.dpi, bbox_inches='tight')
    figIObytes.seek(0)
    data = base64.b64encode(figIObytes.read()).decode()
    return data

def plot_blank():
    fig = plt.figure() 
    # fig.text(0.5, 0.5, 'draft', horizontalalignment='center',
        #  verticalalignment='center', transform=ax.transAxes)
    ax=fig.add_subplot(1,1,1)
    ax.text(0.5, 0.5, 'blank', size=18, color='grey', rotation=45,
            horizontalalignment='center', verticalalignment='center')
    ax.get_xaxis().set_visible(False), ax.get_yaxis().set_visible(False)
    ax.set_frame_on(False)
    return fig

def mzqc_to_single_run_report(mzqc_obj, pre_irt_plot=None):
    """
    compile a html report form the run quality objects of the first listed run in the given file
    """   
    if len(mzqc_obj.runQualities) > 1:
        logger.warning("Functionality only available for single runs, found more than one run. Will produce report for first run only!")

    # collect metric values (lazy)
    name = mzqc_obj.runQualities[0].metadata.inputFiles[0].name
    mz_range = next(iter(list(filter(lambda x: x.accession == "MS:4000069", mzqc_obj.runQualities[0].qualityMetrics)))).value
    rt_range = next(iter(list(filter(lambda x: x.accession == "MS:4000070", mzqc_obj.runQualities[0].qualityMetrics)))).value
    tic = next(iter(list(filter(lambda x: x.accession == "MS:4000104", mzqc_obj.runQualities[0].qualityMetrics)))).value
    conta = next(iter(list(filter(lambda x: x.accession == "MS:4000xx3", mzqc_obj.runQualities[0].qualityMetrics)))).value
    
    if not pre_irt_plot:
        irt_plot = plot_to_b64(plot_blank())
    else: 
        irt_plot = pre_irt_plot

    tic_df = pd.DataFrame(tic)
    f = tic_df.plot.line(y="MS:1000285", x="MS:1000894").get_figure()
    tic_plot = plot_to_b64(f)
    mz_plot = plot_to_b64(plot_range_mz(mz_range))
    rt_plot = plot_to_b64(plot_range_rt(rt_range))
    conta_tab = pd.DataFrame(conta).rename(columns={"MS:1003169": "Contaminant", "MS:1002733": "Spectrum Count"}).to_html(border=1)

    return report_tmplt.format(name=name, mz_plot=mz_plot, rt_plot=rt_plot, irt_plot=irt_plot, tic_plot=tic_plot, conta_tab=conta_tab)

@click.command(short_help='produce a minimal HTML document with metric visualisations of the given mzQC file')
@click.argument('input', type=click.Path(exists=True,readable=True) )  # mzqc
@click.argument('output', type=click.Path(writable=True) )  # html
@click.option('-f', '--fig', 'figure', type=click.Path(exists=False,readable=True),
    required=False, help="A visualisation of the irt calibration.")
def assemble_report(input, output, figure=None):
    if figure:
        with open(figure, "rb") as image_file:
            figure = base64.b64encode(image_file.read()).decode()
    
    with open(input, "r") as file_in:
        with open(output, "w") as file_out:
            mzqcobj = qc.JsonSerialisable.FromJson(file_in)
            report = mzqc_to_single_run_report(mzqcobj, figure)
            file_out.write(report)

if __name__ == '__main__':
    assemble_report()