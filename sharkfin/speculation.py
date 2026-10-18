"""High-speculation themes: early-stage trends that could become the next Micron or SanDisk.

Each theme is a researched thesis (what the bottleneck is, why now, what would prove it, what could kill it)
with a short list of listed ways to play it. ``radar`` reads each theme's price action so the page can say
whether a theme is still quiet, just turning up (the window you want), already running, or cooling off.

The research notes were written in October 2026 from company releases, earnings calls and news coverage
(sources are listed on each theme). They are a watchlist for small, speculative positions, not tested
strategies: none of this has the walk-forward record SharkFin's swing strategies have.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

AS_OF = "October 2026"

# Risk tiers for individual plays
CORE, SPEC, MOON = "Picks & shovels", "Speculative", "Moonshot"
TIER_HELP = {
    CORE: "An established company that sells into the trend. Lower upside, but it survives if the trend is slow.",
    SPEC: "Smaller, more focused on the trend. Can double or halve on one piece of news.",
    MOON: "Early, often losing money and selling stock to fund itself. Size it so losing all of it is fine.",
}


@dataclass(frozen=True)
class Play:
    ticker: str
    name: str
    tier: str
    why: str


@dataclass(frozen=True)
class Theme:
    key: str
    name: str
    tagline: str
    bottleneck: str
    why_now: list
    proof: list
    risks: list
    horizon: str
    plays: list
    sources: list = field(default_factory=list)
    from_you: bool = False   # one of the themes from Adi's long-term book


THEMES: list[Theme] = [
    Theme(
        "optics", "Light instead of copper",
        "AI clusters are running out of room to move data with copper. Lasers and co-packaged optics take over.",
        "Laser and optical-engine capacity. NVIDIA prepaid suppliers to lock it up, the same thing that happened "
        "with memory before Micron's run.",
        ["NVIDIA committed about $2B each to Lumentum and Coherent in March 2026 for laser supply and future capacity.",
         "Broadcom's 51.2T co-packaged switch moved into limited mass production in mid-2026 (TrendForce).",
         "Scale-out CPO revenue starts in 2H 2026; the much bigger scale-up wave follows in 2027-28 (Coherent, Lumentum)."],
        ["Lumentum and Coherent raising laser capacity guidance again", "Scale-up CPO design wins announced for 2027 GPUs",
         "Optical engine yields improving (TrendForce flags yield as the gate)"],
        ["The Oct 14-15 selloff showed optics fall hardest when AI funding fears flare",
         "Copper keeps winning short links longer than expected", "Chinese laser makers add capacity"],
        "6-24 months",
        [Play("LITE", "Lumentum", CORE, "Indium-phosphide lasers; NVIDIA prepaid for capacity."),
         Play("COHR", "Coherent", CORE, "Lasers and transceivers; forward P/E fell from 53x to ~32x while estimates rose."),
         Play("AAOI", "Applied Optoelectronics", SPEC, "US-made transceivers; swings 7-10% on any AI headline."),
         Play("POET", "POET Technologies", MOON, "Optical interposer for co-packaged optics; tiny revenue so far.")],
        ["https://siliconangle.com/2026/03/02/nvidia-invests-4b-co-packaged-optics-suppliers-lumentum-coherent/",
         "https://trendforce.com/presscenter/news/20260727-13151.html"]),
    Theme(
        "power", "Power behind the meter",
        "Data centers can't wait years for the grid, so they build their own power on site.",
        "Grid hookups and gas turbines are sold out for years. On-site fuel cells and storage ship in weeks.",
        ["Brookfield expanded its Bloom Energy financing from $5B to $25B in July 2026 for AI power projects.",
         "Hedge funds holding Bloom rose from 91 to 116 in Q2 2026 (Insider Monkey 13F count).",
         "Turbine makers quote multi-year delivery slots; utilities are rationing new data-center hookups."],
        ["More hyperscaler orders announced for on-site power", "Bloom margins rising as volume grows",
         "Turbine backlogs keep lengthening"],
        ["Already a crowded trade after a big 2025-26 run", "Natural gas prices", "Grid build-outs catching up by 2028-29"],
        "Now-18 months",
        [Play("GEV", "GE Vernova", CORE, "Gas turbines and grid gear, sold out for years."),
         Play("NVT", "nVent", CORE, "Power distribution and liquid cooling for racks (from your book)."),
         Play("BE", "Bloom Energy", SPEC, "Fuel cells that power a data center in weeks; Brookfield's $25B partner."),
         Play("FLNC", "Fluence Energy", SPEC, "Grid batteries that let sites run harder on a capped hookup.")],
        ["https://www.microgridknowledge.com/generation-fuels/news/55388215/brookfield-quintupling-capitalization-of-bloom-energy-fuel-cells-for-ai-to-25b",
         "https://www.insidermonkey.com/blog/ai-fueled-demand-signals-a-bigger-opportunity-for-bloom-energy-be-investors-1805579/"],
        from_you=True),
    Theme(
        "nuclear", "Nuclear fuel and small reactors",
        "Every new reactor design needs a fuel only one US company can make today.",
        "High-assay low-enriched uranium (HALEU). Centrus is the only US-licensed producer; Russia was the old supplier.",
        ["NuScale is the only SMR design with US approval; Oklo's Aurora passed a DOE safety review.",
         "Oklo and Centrus are in talks on fuel for a planned 1.2 GW campus in Ohio.",
         "Nuclear names topped trading-volume screens in early October 2026 (MarketBeat)."],
        ["First NRC construction licences for advanced reactors", "Long-term HALEU contracts signed",
         "A hyperscaler power-purchase deal tied to an SMR"],
        ["First reactors are 2027-30 at best; delays are the norm", "Share sales to fund construction",
         "Very volatile: SMR stocks have halved and doubled within a year"],
        "1-4 years",
        [Play("BWXT", "BWX Technologies", CORE, "Sole supplier of Navy reactors, building HALEU capacity (from your book)."),
         Play("LEU", "Centrus Energy", SPEC, "The only US-licensed HALEU producer."),
         Play("OKLO", "Oklo", MOON, "Aurora micro-reactors; no licensed reactor yet."),
         Play("SMR", "NuScale Power", MOON, "The one approved SMR design, still looking for its first firm buyer.")],
        ["https://www.cmcmarkets.com/en/optox/three-nuclear-stocks-that-could-ride-the-ai-power-crunch",
         "https://www.marketbeat.com/instant-alerts/list-best-nuclear-stocks-to-watch-now-october-12th-2026-10-12/"],
        from_you=True),
    Theme(
        "fusion", "Fusion's supply chain",
        "Own the superconducting tape every magnet-based fusion machine needs, not the long-shot reactors.",
        "High-temperature superconducting (HTS) tape. Commonwealth Fusion placed a record 10,000 km order with "
        "Fujikura in September 2026.",
        ["SPARC's magnets are being installed for first plasma in 2027.",
         "Commonwealth Fusion has raised about $3.9B; Google agreed to buy half of ARC's output.",
         "General Fusion listed on Nasdaq in July 2026 and hit a 1.1 keV milestone with UKAEA in October."],
        ["SPARC first plasma, then a Q>1 result (roughly 20-30% odds in 2027 by your book's estimate)",
         "More HTS tape orders from other fusion and grid-cable buyers"],
        ["Fusion timelines always slip", "Fujikura trades on AI fiber, not fusion",
         "General Fusion is likely to sell more stock"],
        "2-6 years",
        [Play("5803.T", "Fujikura (Tokyo)", CORE, "HTS tape plus AI fiber; fusion is upside, not the whole bet."),
         Play("GFUZ", "General Fusion", MOON, "Magnetized-target fusion; first plant targeted around 2035.")],
        ["https://www.khaleejtimes.com/business/us-fusion-firm-orders-record-10000km-of-superconducting-tape-from-japans-fujikura",
         "https://www.gov.uk/government/news/ukaea-general-fusion-announce-magnetised-target-fusion-milestone"],
        from_you=True),
    Theme(
        "packaging", "Advanced chip packaging and glass",
        "Chips are now built by stacking dies, and the packaging step, not the chip itself, is the choke point.",
        "Advanced packaging capacity (CoWoS-style) and, from 2027, glass substrates that let chips get bigger.",
        ["TrendForce expects TSMC, Samsung, Rapidus, SK Absolics and Intel to mass-produce glass substrates in 2027-28.",
         "Intel showed a glass-substrate package twice the reticle size in January 2026.",
         "TrendForce names advanced packaging capacity a key limit on co-packaged optics output too."],
        ["Glass-substrate equipment orders in 2027", "Packaging capex guides raised again",
         "HBM4 stacks needing more hybrid bonding"],
        ["Capex cycles turn fast; equipment makers fall first in a slowdown", "Glass yields slip into 2029"],
        "1-3 years",
        [Play("AMKR", "Amkor Technology", CORE, "Largest US-listed packaging house, building in Arizona."),
         Play("ONTO", "Onto Innovation", CORE, "Inspection tools for advanced packaging and panels."),
         Play("CAMT", "Camtek", SPEC, "Inspection for HBM and chiplets."),
         Play("LPK.DE", "LPKF Laser (Germany)", MOON, "Laser glass-drilling tools; says 2027 is the ramp year.")],
        ["https://www.trendforce.com/research/download/RP260224KD",
         "https://quartr.com/events/lpkf-laser-electronics-ag-lpk-investor-presentation_oCWOYE9x"]),
    Theme(
        "minerals", "Rare earths and critical minerals",
        "China controls the magnets and metals every motor, drone and missile needs. The US is paying to change that.",
        "Separated rare earths and magnets, plus gallium and antimony, where China has used export bans.",
        ["The Pentagon set a price floor for MP Materials' rare earths in July 2025.",
         "USA Rare Earth secured $3.1B in January 2026, with the government taking a 10% stake.",
         "China's gallium export suspension is scheduled to end Nov 27, 2026: an extension would be the next catalyst."],
        ["New government offtakes or equity stakes", "MP's heavy rare-earth separation starting",
         "Magnet plants hitting production"],
        ["Policy-driven: a US-China deal can knock 30% off in a day", "Long build times and dilution"],
        "1-3 years",
        [Play("MP", "MP Materials", CORE, "The main US rare-earth mine and magnet maker, with a Pentagon price floor."),
         Play("UUUU", "Energy Fuels", SPEC, "Uranium miner now separating heavy rare earths."),
         Play("USAR", "USA Rare Earth", MOON, "Mine-to-magnet plan backed by a government stake."),
         Play("UAMY", "United States Antimony", MOON, "One of the few non-Chinese antimony processors.")],
        ["https://www.nasdaq.com/articles/3-rare-earth-stocks-watch-2026"]),
    Theme(
        "quantum", "Quantum computing",
        "Still pre-profit, but the first $100M+ revenue quantum companies exist and the big IPO is done.",
        "Error-corrected qubits. Whoever gets logical qubits to scale first sets the standard.",
        ["Quantinuum IPO'd in June 2026 at about $60 (QNT); it trades near $37 now, 57% off its high.",
         "IonQ guided 2026 revenue to $225-245M; D-Wave bookings jumped to $33M in Q1.",
         "Quantinuum's insider lockup ends around Dec 1, 2026, which usually weighs on price."],
        ["Logical-qubit milestones with low error rates", "Government and pharma contracts",
         "Quantinuum after its lockup (your book's entry point)"],
        ["Revenue is tiny next to valuations", "Constant share sales", "Breakthrough headlines that don't pan out"],
        "2-5 years",
        [Play("QNT", "Quantinuum", SPEC, "The best-funded trapped-ion leader (from your book; wait for the lockup)."),
         Play("IONQ", "IonQ", SPEC, "The first quantum pure play past $100M in revenue."),
         Play("RGTI", "Rigetti Computing", MOON, "Superconducting qubits; $569M cash, small revenue."),
         Play("QBTS", "D-Wave Quantum", MOON, "Annealing machines; bookings rising faster than revenue.")],
        ["https://finance.yahoo.com/markets/article/honeywells-quantinuums-ipo-puts-the-quantum-stock-rally-to-the-test-154531114.html"],
        from_you=True),
    Theme(
        "space", "Space: phones and data centers in orbit",
        "Satellites that talk straight to your phone, and the first serious plans to put AI compute in orbit.",
        "Launch capacity. SpaceX's IPO has pulled money into the whole sector; launch slots decide who ships.",
        ["AST SpaceMobile has FCC approval for direct-to-phone broadband; commercial service slid to early 2027.",
         "Starcloud (private) doubled its valuation to $2.3B in August 2026 with NVIDIA investing.",
         "SpaceX plans to spend part of its IPO money on orbital data centers from about 2028."],
        ["AST's satellite launches staying on schedule", "Carrier contracts and first paid service",
         "Rocket Lab's Neutron first flight"],
        ["Launch delays push revenue out a year at a time", "Big convertible raises dilute holders"],
        "1-3 years",
        [Play("RKLB", "Rocket Lab", SPEC, "The number-two US launcher plus satellite parts."),
         Play("ASTS", "AST SpaceMobile", MOON, "Direct-to-phone broadband; service starts early 2027 if launches hold.")],
        ["https://developingtelecoms.com/telecom-technology/satellite-communications-networks/20554-ast-spacemobile-service-launch-delayed.html",
         "https://www.bnnbloomberg.ca/business/company-news/2026/08/21/orbital-data-center-startup-starcloud-valued-at-us23-billion-in-latest-funding/"]),
    Theme(
        "robots", "Humanoid robots",
        "Tesla says Optimus goes on sale by the end of 2027. The parts makers get paid first.",
        "Actuators, reducers and roller screws for the joints, mostly made in China today.",
        ["Tesla's Optimus output reportedly rose about tenfold in mid-2026, with hands still the weak spot.",
         "Morgan Stanley puts humanoid components at a $780B revenue opportunity by 2040.",
         "Omdia counted 13,000 humanoids shipped in 2025, most of them in China."],
        ["Tesla putting a price and date on Optimus sales", "Non-Chinese actuator suppliers winning orders"],
        ["Hype runs years ahead of real sales", "Most suppliers are Chinese and hard to buy from the US"],
        "2-5 years",
        [Play("TSLA", "Tesla", CORE, "The highest-profile humanoid program, inside a car company."),
         Play("6324.T", "Harmonic Drive Systems (Tokyo)", SPEC, "Precision reducers for robot joints."),
         Play("AMBA", "Ambarella", SPEC, "Low-power vision chips for robots and drones.")],
        ["https://www.roic.ai/news/teslas-optimus-robot-ramps-up-production-tenfold-but-hand-and-forearm-issues-linger-09-25-2026",
         "https://www.cmcmarkets.com/en/optox/humanoid-robots-which-stocks-are-leading-the-way"]),
    Theme(
        "drones", "Drones and counter-drones",
        "Cheap drones changed warfare; the 2027 US budget asks for about $75B for drones and drone defense.",
        "Production capacity for small drones and counter-drone systems the Pentagon can buy fast.",
        ["The 2027 defense request includes nearly $75B for unmanned systems and counter-drone tech.",
         "Drone stocks fell 30%+ in early 2026 while backlogs kept growing: a gap between price and orders.",
         "Ondas' counter-drone unit won World Cup venue contracts."],
        ["Budget passing with the drone money intact", "Large program-of-record awards", "Backlog turning into revenue"],
        ["Lost contracts (AeroVironment cut $1.7B from its outlook)", "Budget fights and continuing resolutions"],
        "6-24 months",
        [Play("KTOS", "Kratos Defense", CORE, "Jet drones and hypersonics; revenue up 46% in Q1."),
         Play("AVAV", "AeroVironment", SPEC, "Switchblade and counter-drone; down after a contract loss."),
         Play("ONDS", "Ondas Holdings", MOON, "Autonomous drones and counter-drone systems."),
         Play("RCAT", "Red Cat", MOON, "Small reconnaissance drones for the Army.")],
        ["https://www.marketbeat.com/articles/drone-stocks-are-down-but-defense-backlogs-tell-a-different-story/"]),
    Theme(
        "biotech", "AI-discovered drugs",
        "The first drugs designed with AI are reaching real trial readouts. A win re-rates the whole group.",
        "Clinical proof. Until AI-designed drugs beat old-style ones in trials, the group trades as a promise.",
        ["Relay, AbCellera and Recursion all have readouts between late 2026 and 2027 (your book).",
         "Biotech held up during the Oct 14-15 AI selloff: XBI rose 2% while chips fell 5-14%.",
         "The group barely moves with chips, so it diversifies an AI-heavy book."],
        ["AbCellera's Oct 22 data", "Relay's next trial update", "Recursion's 2H 2027 readout"],
        ["Binary: one failed trial can halve a stock", "Recursion just sold $200M of stock"],
        "6-24 months",
        [Play("XBI", "Biotech ETF", CORE, "The calm way to own the theme."),
         Play("RLAY", "Relay Therapeutics", SPEC, "Best trial setup of the AI-bio names in your book."),
         Play("ABCL", "AbCellera", SPEC, "Antibody discovery; data due Oct 22."),
         Play("RXRX", "Recursion", MOON, "Wait for its stock sale to settle (mid-November).")],
        [], from_you=True),
    Theme(
        "batteries", "Next-generation batteries",
        "Sodium-ion and solid-state cells could cut costs and fire risk for grid storage and cars.",
        "Cheap, safe grid storage for data centers and solar. Lithium supply is the old constraint.",
        ["CATL is mass-producing sodium-ion cells and is your book's best diversifier (0.19 correlation with chips).",
         "QuantumScape launched its Eagle Line pilot production in 2026 and added Honda's R&D arm as a partner.",
         "Grid storage demand is rising with data-center power needs."],
        ["CATL's Q3 results on Oct 20", "QuantumScape shipping B-samples to customers"],
        ["QuantumScape may not be commercial until 2029", "Chinese price wars", "US tariffs on Chinese batteries"],
        "1-4 years",
        [Play("3750.HK", "CATL (Hong Kong)", CORE, "World's largest battery maker, leading on sodium-ion."),
         Play("QS", "QuantumScape", MOON, "Solid-state cells; years from real revenue.")],
        ["https://www.fool.com/investing/2026/07/05/why-did-quantumscape-stock-drop-30-in-2026/"],
        from_you=True),
]

THEME_BY_KEY = {t.key: t for t in THEMES}

# The run the section is built around: what Micron and SanDisk looked like before memory took off.
CASE_STUDY = ("MU", "SNDK")
CASE_NOTES = [
    ("Spring 2025: a shortage nobody priced", "Memory makers said AI servers needed far more DRAM and flash than they "
     "could build. Micron traded near its 200-day line, below where it was a year earlier."),
    ("Summer 2025: the turn", "Contract prices rose, Micron raised guidance and the stock reclaimed its 200-day with "
     "rising strength against the S&P 500. This is the stage SharkFin's radar calls Turning up."),
    ("2026: everyone knows", "Musk called memory AI's biggest bottleneck; Micron rose more than 10x from its 2025 low "
     "and SanDisk 600%+ in 2026 alone. By then the stage is Running, and the risk is buying the top."),
]

STAGES = {
    "Quiet": ("Below its 200-day and lagging the S&P 500. The story may be early, but the market isn't buying it yet.", "neu"),
    "Turning up": ("Back above its 200-day, beating the S&P 500 over 6 months, and not yet up a lot over 12. "
                   "This is the window you want: the market has started to notice.", "pos"),
    "Running": ("Up a lot over 12 months and near its high. The trend is real, but most of the easy money is made.", "info"),
    "Cooling": ("Pulling back after a big run, or back under its 200-day. Wait for it to turn up again.", "neg"),
}
STAGE_ORDER = ["Turning up", "Running", "Quiet", "Cooling"]
RUN_12M = 0.60       # up more than this over a year counts as a run
NEAR_HIGH = 0.15     # within this of the 52-week high


def all_tickers() -> list[str]:
    out = []
    for t in THEMES:
        out += [p.ticker for p in t.plays]
    return list(dict.fromkeys(out + list(CASE_STUDY)))


def stats(close: pd.Series, bench: pd.Series | None = None) -> dict:
    """Trend readings for one price series (daily closes)."""
    c = close.dropna().astype(float)
    if len(c) < 60:
        return {}
    last = float(c.iloc[-1])
    ago = lambda n: float(c.iloc[-n - 1]) if len(c) > n else np.nan
    sma200 = float(c.iloc[-200:].mean()) if len(c) >= 200 else float(c.mean())
    hi = float(c.iloc[-252:].max())
    out = {"price": last, "1m": last / ago(21) - 1, "3m": last / ago(63) - 1, "6m": last / ago(126) - 1,
           "12m": last / ago(252) - 1, "vs200": last / sma200 - 1, "off_high": last / hi - 1,
           "peak_run": hi / float(c.iloc[-252:].iloc[0]) - 1,
           "vol": float(c.pct_change().iloc[-63:].std() * np.sqrt(252))}
    if bench is not None:
        b = bench.dropna().astype(float).reindex(c.index).ffill()
        if len(b.dropna()) > 126:
            out["rs6m"] = out["6m"] - (float(b.iloc[-1]) / float(b.iloc[-127]) - 1)
    out["stage"] = stage(out)
    return out


def stage(s: dict) -> str:
    """Quiet / Turning up / Running / Cooling from a ``stats`` row (see ``STAGES``)."""
    vs200, r12, off, rs = (s.get(k, np.nan) for k in ("vs200", "12m", "off_high", "rs6m"))
    if not np.isfinite(vs200):
        return "Quiet"
    if vs200 < 0:
        peak = s.get("peak_run", np.nan)
        ran = (np.isfinite(r12) and r12 > RUN_12M) or (np.isfinite(peak) and peak > RUN_12M and np.isfinite(off) and off < -0.2)
        return "Cooling" if ran else "Quiet"
    if np.isfinite(r12) and r12 > RUN_12M and np.isfinite(off) and off > -NEAR_HIGH:
        return "Running"
    if np.isfinite(r12) and r12 > RUN_12M:
        return "Cooling"   # still above the 200-day, but pulling back from a big run
    if not np.isfinite(rs) or rs > 0:
        return "Turning up"
    return "Quiet"


def stage_history(close: pd.Series, bench: pd.Series | None = None, step: int = 5) -> pd.Series:
    """The stage at every ``step``-th day, each read only from prices up to that day."""
    c = close.dropna()
    out = {}
    for i in range(252, len(c), step):
        s = stats(c.iloc[: i + 1], bench.loc[: c.index[i]] if bench is not None else None)
        if s:
            out[c.index[i]] = s["stage"]
    return pd.Series(out, dtype=object)


def radar(close: pd.DataFrame, bench: pd.Series | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-play readings and per-theme readings (an equal-weight basket of each theme's plays)."""
    rows, trows = [], []
    for t in THEMES:
        syms = [p.ticker for p in t.plays if p.ticker in close and close[p.ticker].dropna().size >= 60]
        for p in t.plays:
            s = stats(close[p.ticker], bench) if p.ticker in syms else {}
            rows.append({"Theme": t.name, "key": t.key, "Ticker": p.ticker, "Company": p.name, "Tier": p.tier,
                         "Why": p.why, **s})
        if syms:
            # Equal-weight daily returns of whichever members trade that day, so a late listing joins smoothly.
            sub = close[syms].dropna(how="all")
            rets = sub.pct_change(fill_method=None).mean(axis=1).fillna(0.0)
            basket = (1 + rets).cumprod()
            trows.append({"Theme": t.name, "key": t.key, "n": len(syms), **stats(basket, bench)})
    plays = pd.DataFrame(rows)
    themes = pd.DataFrame(trows)
    return plays, themes
