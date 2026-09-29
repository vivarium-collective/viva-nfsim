"""Visualization Step subclasses for pbg-nfsim.

Visualizations follow the viva-superpowers convention (v0.4.15+):
each subclass overrides `update()` to consume per-step state via wires
(like an Emitter), accumulates history internally, and returns
``{'html': '<rendered figure>'}`` each step. The composite spec wires
the input ports to store paths.

See viva_superpowers.visualization for the base-class contract.
"""
from __future__ import annotations

from viva_superpowers.visualization import Visualization


class FlagellaAssemblyPlots(Visualization):
    """Time-series HTML plot of NFSim flagella-assembly observables.

    Consumes the shared ``species`` map (the store all NFSim composites
    wire to) at each step, accumulates per-species trajectories across
    calls, and emits a Plotly HTML figure on every update. Downstream
    consumers (dashboards, notebook viewers) read the latest ``html``
    from the wired store.

    The species map is bucketed into three traces by name prefix so the
    figure stays readable:

    * ``Free_*``     — monomer pools fed by MonomerProduction
    * ``Growing_*``  — in-flight assembly intermediates
    * everything else — finished complexes
    """

    config_schema = {
        'title': {'_type': 'string', '_default': 'Flagella assembly'},
        'max_traces': {'_type': 'integer', '_default': 12},
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.times: list[float] = []
        # species_name -> list[float] (one entry per recorded time)
        self.history: dict[str, list[float]] = {}

    def inputs(self):
        return {
            'species': 'map[float]',
            'time': 'float',
        }

    def update(self, state, interval=1.0):
        species = state.get('species') or {}
        t = float(state.get('time', len(self.times) * (interval or 1.0)))
        self.times.append(t)
        step_idx = len(self.times) - 1
        # Pad any newly seen species with zeros up to this step.
        for name, val in species.items():
            if name not in self.history:
                self.history[name] = [0.0] * step_idx
            self.history[name].append(float(val) if val is not None else 0.0)
        # Pad species that were absent this step.
        for name, hist in self.history.items():
            if len(hist) < step_idx + 1:
                hist.append(hist[-1] if hist else 0.0)

        title = (self.config or {}).get('title', 'Flagella assembly')
        max_traces = int((self.config or {}).get('max_traces', 12))

        # Rank species by peak value so the busiest traces win when we
        # cap the legend.
        ranked = sorted(
            self.history.items(),
            key=lambda kv: max(kv[1]) if kv[1] else 0.0,
            reverse=True,
        )[:max_traces]

        traces = []
        for name, ys in ranked:
            traces.append(
                '{"x":' + repr(self.times) + ',"y":' + repr(ys) +
                ',"type":"scatter","mode":"lines","name":"' + name + '"}'
            )
        html = (
            f'<div id="fap" style="height:380px"></div>'
            f'<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>'
            f'<script>Plotly.newPlot("fap",[{",".join(traces)}],'
            f'{{title:"{title}",margin:{{l:55,r:15,t:35,b:40}},'
            f'xaxis:{{title:"time (s)"}},'
            f'yaxis:{{title:"count"}},'
            f'legend:{{orientation:"h",y:-0.2}}}},'
            f'{{responsive:true,displayModeBar:false}});</script>'
        )
        return {'html': html}
