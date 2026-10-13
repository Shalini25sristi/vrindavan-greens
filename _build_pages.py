#!/usr/bin/env python3
import re, json, html as _html, os

SRC = "_src.html"
src = open(SRC, encoding="utf-8").read()

# ---------- pull shared pieces ----------
head_html = re.search(r"<head>(.*?)</head>", src, re.S).group(1)
body = re.search(r"<body>(.*?)</body>", src, re.S).group(1)

css = "\n".join(re.findall(r"<style>(.*?)</style>", head_html, re.S))

scripts = re.findall(r"<script>(.*?)</script>", body, re.S)      # [analytics? none, map+form, audio, ext]
# locate the three big inline scripts by markers
def find_script(marker):
    for s in scripts:
        if marker in s:
            return s
    raise SystemExit("script not found: " + marker)

s0 = find_script("register your interest")       # data + map + form
s1 = find_script("vrindavanFlute")               # audio
s2 = find_script("VG: extension behaviours")     # extension

# ---------- audio / sound toggle markup ----------
sound_markup = re.search(r"<button class=\"sound-toggle\".*?</audio>", body, re.S).group(0)

# ---------- brand ----------
brand = re.search(r'<a href="#top" class="brand">.*?</a>', body, re.S).group(0)
brand = brand.replace('href="#top"', 'href="index.html"')

# ---------- hero ----------
hero = re.search(r'<header class="hero".*?</header>', body, re.S).group(0)

# ---------- actionbar + floating wa ----------
actionbar = re.search(r'<div class="actionbar".*?</div>', body, re.S).group(0)
actionbar = actionbar.replace('href="#contact" data-intent="visit"', 'href="contact.html?intent=visit"')
actionbar = actionbar.replace('href="#contact"', 'href="contact.html"')
wa_float = re.search(r'<a class="wa-float".*?</a>', body, re.S).group(0)

# ---------- top-level sections ----------
sec_re = re.compile(r'<section\b|</section>')
depth = 0; start = None; sections = {}
for m in sec_re.finditer(body):
    if m.group(0) == '<section':
        if depth == 0:
            start = m.start()
        depth += 1
    else:
        depth -= 1
        if depth == 0 and start is not None:
            block = body[start:m.end()]
            idm = re.search(r'<section[^>]*\bid="([^"]+)"', block)
            if idm:
                sections[idm.group(1)] = block
            start = None

# ---------- data (for hero numbers) ----------
di = s0.find("const D =")
dj = s0.find("{", di)
D, _ = json.JSONDecoder().raw_decode(s0[dj:])
plots = [f for f in D["features"] if f.get("kind") == "plot"]
avail = [f for f in plots if f.get("status") != "Sold" and f.get("kind") == "plot" and f.get("status") != "Provisional"]
avail = [f for f in plots if f.get("status") not in ("Sold",)]
total_katha = round(sum(f.get("katha", 0) for f in plots))
hero = hero.replace(">166<", ">%d<" % len(plots))
hero = hero.replace(">498<", ">%d<" % total_katha)
hero = re.sub(r'(<span id="tLimited">).*?(</span>)', r'\g<1>%d plots currently available\g<2>' % len(avail), hero)

# ---------- split map/data vs register form ----------
ridx = s0.find("/* ---------- register your interest ---------- */")
data_map = s0[:ridx]
register = s0[ridx:]
# move trailing standalone refresh() into data_map
m = re.search(r'\n\s*refresh\(\);\s*$', register)
if m:
    data_map = data_map.rstrip() + "\n\nrefresh();\n"
    register = register[:m.start()]

# card() CTA -> contact page with plot prefill
data_map = data_map.replace(
    'href="#contact" data-intent="visit">Book a visit to ${f.id}',
    'href="contact.html?intent=visit&plot=${encodeURIComponent(f.id)}" data-intent="visit">Book a visit to ${f.id}')

# inject contact deeplink into register IIFE
anchor = "window.prefillPlot=id=>{ const f=g('rPlot'); if(f) f.value=id||''; };"
inject = anchor + """
  /* deep link: contact.html?intent=visit&plot=B%2F1 */
  try{
    const q=new URL(location.href).searchParams;
    const want=q.get('intent');
    if(want){ state.intent=want;
      const host=g('rIntent');
      if(host){ [...host.children].forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.v===want))); }
      const pw=g('pickWrap'); if(pw) pw.hidden=(want!=='pickup');
    }
    const pl=q.get('plot'); if(pl){ const pf=g('rPlot'); if(pf) pf.value=pl; }
  }catch(_){}
"""
register = register.replace(anchor, inject)

# ---------- split extension script ----------
markers = ["EMI calculator", "interactive home configurator", "brochure (lead capture)",
           "virtual tour (on demand)", "deep-linkable plots, sharing, live holds"]
ext = {}
for i, mk in enumerate(markers):
    s = s2.find("/* ---------- " + mk)
    e = s2.find("/* ---------- " + markers[i + 1]) if i + 1 < len(markers) else len(s2)
    ext[mk] = s2[s:e]
# tour fallback link -> contact page
ext["virtual tour (on demand)"] = ext["virtual tour (on demand)"].replace('href="#contact"', 'href="contact.html"')
# share link: no hash
ext["deep-linkable plots, sharing, live holds"] = ext["deep-linkable plots, sharing, live holds"].replace("u.hash='plots';", "u.hash='';")

# ---------- link rewriting ----------
FRAG = {"top": "index.html", "idea": "index.html", "location": "location.html",
        "plots": "plots.html", "plans": "plans.html", "pricing": "pricing.html",
        "club": "amenities.html", "why": "why.html", "tour": "tour.html",
        "stories": "stories.html", "loan": "loan.html", "faq": "faq.html",
        "contact": "contact.html", "trust": "contact.html#trust"}

def rewrite(h):
    h = h.replace('href="#contact" data-intent="visit"', 'href="contact.html?intent=visit" data-intent="visit"')
    h = h.replace('data-intent="visit" href="#contact"', 'data-intent="visit" href="contact.html?intent=visit"')
    h = h.replace('href="#contact" data-intent="call"', 'href="contact.html?intent=call" data-intent="call"')
    h = h.replace('href="#contact"', 'href="contact.html"')
    for frag, page in FRAG.items():
        h = h.replace('href="#%s"' % frag, 'href="%s"' % page)
    return h

# ---------- extra css ----------
EXTRA_CSS = """
/* ===== multi-page navigation + page furniture ===== */
nav a[aria-current="page"]{color:var(--tulsi)!important;border-color:var(--marigold)!important}
.nav-more{position:relative}
.nav-more>summary{list-style:none;cursor:pointer;color:var(--muted);font:500 13.5px/1 var(--ui);letter-spacing:.04em;padding:7px 0;display:inline-flex;align-items:center;gap:6px;border-bottom:1.5px solid transparent}
.nav-more>summary::-webkit-details-marker{display:none}
.nav-more[open]>summary,.nav-more>summary:hover{color:var(--forest);border-color:var(--marigold)}
.nav-more .menu{position:absolute;right:0;top:32px;min-width:212px;background:var(--paper);border:1px solid var(--rule);box-shadow:0 14px 30px rgba(20,50,35,.16);display:grid;z-index:95}
.nav-more .menu a{padding:12px 15px;border-bottom:1px solid var(--rule);color:var(--forest);text-decoration:none;font:600 13px/1.2 var(--ui)}
.nav-more .menu a:last-child{border-bottom:none}
.nav-more .menu a:hover{background:var(--sandal)}
.nav-more .menu a[aria-current="page"]{background:var(--sandal);color:var(--tulsi)}
@media(max-width:980px){.nav-more{display:none}}
.pagebar{background:var(--paper);border-bottom:1px solid var(--rule);padding:15px 0}
.pagebar .wrap{font:600 11px/1 var(--ui);letter-spacing:.14em;text-transform:uppercase;color:var(--gold-deep)}
.pagebar a{color:var(--gold-deep);text-decoration:none}
.pagebar a:hover{color:var(--marigold)}
.explore{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:10px}
.explore a{display:block;text-decoration:none;background:var(--paper);border:1px solid var(--rule);border-top:2px solid var(--marigold);padding:22px;color:var(--ink);transition:transform .18s,border-color .18s}
.explore a:hover{transform:translateY(-3px);border-top-color:var(--peacock)}
.explore .n{display:block;font-family:var(--mono);font-size:11px;color:var(--marigold);letter-spacing:.16em;margin-bottom:10px}
.explore b{display:block;font-family:var(--display);font-size:20px;color:var(--tulsi);margin-bottom:6px}
.explore span{font-size:14px;color:var(--muted)}
.gallery{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.gallery figure{margin:0}
.gallery img{display:block;width:100%;height:230px;object-fit:cover;border:1px solid var(--rule);background:var(--dawn)}
.gallery figcaption{font-size:12.5px;color:var(--muted);padding:8px 2px}
.footnav{display:grid;grid-template-columns:repeat(3,1fr);gap:8px 22px;max-width:640px}
.footnav a{color:#9DB4A2;text-decoration:none;font-size:12.5px}
.footnav a:hover{color:#fff}
.btn-gold,.btn-ghost{display:inline-block;text-decoration:none}
@media(max-width:940px){.explore{grid-template-columns:1fr 1fr}.gallery{grid-template-columns:1fr 1fr}.footnav{grid-template-columns:1fr 1fr}}
@media(max-width:560px){.explore,.gallery{grid-template-columns:1fr}}
"""

# ---------- nav / footer ----------
PRIMARY = [("index.html", "Home"), ("location.html", "Location"), ("plots.html", "Choose a plot"),
           ("plans.html", "Home plans"), ("pricing.html", "Pricing"), ("amenities.html", "What you share")]
MORE = [("why.html", "Why here"), ("tour.html", "Walk the site"), ("stories.html", "Family stories"),
        ("loan.html", "Loan support"), ("faq.html", "FAQ")]
ALLNAV = PRIMARY + MORE + [("contact.html", "Contact")]

def cur(page, file):
    return ' aria-current="page"' if file == page else ""

def build_nav(page):
    lis = "".join('<li><a href="%s"%s>%s</a></li>' % (f, cur(page, f), t) for f, t in PRIMARY)
    more = "".join('<a href="%s"%s>%s</a>' % (f, cur(page, f), t) for f, t in MORE)
    lis += '<li class="nav-more-item"><details class="nav-more"><summary>More &#9662;</summary><div class="menu">%s</div></details></li>' % more
    mob = "".join('<a href="%s"%s>%s</a>' % (f, cur(page, f), t) for f, t in ALLNAV)
    return ('<nav><div class="wrap">%s<ul>%s</ul>'
            '<a class="cta" href="contact.html?intent=visit">Book a site visit</a>'
            '<details class="mobile-nav"><summary aria-label="Open section menu">&#9776;</summary>'
            '<div class="mobile-nav-panel">%s</div></details></div></nav>' % (brand, lis, mob))

def build_footer():
    links = "".join('<a href="%s">%s</a>' % (f, t) for f, t in ALLNAV)
    return ('<footer><div class="wrap">'
            '<div><strong style="color:#D7E4D8">Vrindavan Greens</strong><br>Alaipur, Madanpur, Nadia<br>'
            '<a href="tel:+919051622888" style="color:#D7E4D8;text-decoration:none">90516 22888</a></div>'
            '<nav class="footnav" aria-label="All pages">%s</nav>'
            '</div><div class="wrap" style="display:block;margin-top:22px">'
            '<div class="disc">Plot availability can change. Illustrations and home-plan visuals are '
            'indicative and subject to site conditions, statutory requirements and final design. Please '
            'verify current inventory and project details with the sales team before making a decision.</div>'
            '</div></footer>' % links)

# ---------- pagebar ----------
def pagebar(label):
    return '<div class="pagebar"><div class="wrap"><a href="index.html">Vrindavan Greens</a> &nbsp;&middot;&nbsp; %s</div></div>' % label

# ---------- explore grid (home) ----------
EXPLORE = [
    ("01", "location.html", "Where it is", "The station, Kalyani, hospitals and schools &mdash; all within fifteen minutes."),
    ("02", "plots.html", "Choose a plot", "An interactive, colour-coded site plan of all 166 plots. Tap any plot for its details."),
    ("03", "plans.html", "Home plans", "Pick a plan for your plot size, then sketch your own with the configurator."),
    ("04", "pricing.html", "Pricing", "Indicative starting price, a payment schedule and an EMI calculator."),
    ("05", "amenities.html", "What you share", "Mandir, maidan, clubhouse, gym, pool and the pond area &mdash; all looked after for you."),
    ("06", "why.html", "Why here", "In Nadia, Vrindavan came to us &mdash; the soil Bengal built its devotion on."),
    ("07", "tour.html", "Walk the site", "A 360&deg; walk through the layout, plus a gallery of the site and homes."),
    ("08", "stories.html", "Family stories", "What early families say about buying and building here."),
    ("09", "loan.html", "Loan support", "Plot loan now, construction loan later &mdash; and help with the paperwork."),
    ("10", "faq.html", "Questions", "Approvals, timelines, maintenance and everything else buyers ask."),
    ("11", "contact.html", "Contact &amp; visit", "Book a site visit, arrange a pick-up, or call the sales desk."),
    ("12", "faq.html", "Documents", "Registration, title flow, mutation and the approvals you should ask to see."),
]
explore_cards = "".join(
    '<a href="%s"><span class="n">%s</span><b>%s</b><span>%s</span></a>' % (h, n, t, d)
    for n, h, t, d in EXPLORE)
explore_section = ('<section id="explore"><div class="wrap">'
                   '<div class="head center"><span class="eyebrow">Explore the community</span>'
                   '<h2>Everything, one tap away.</h2>'
                   '<p>Vrindavan Greens is laid out across clear pages &mdash; the site plan, the home plans, '
                   'the price and the paperwork. Go straight to what matters to you.</p></div>'
                   '<div class="explore">%s</div></div></section>' % explore_cards)

# ---------- page definitions ----------
JSONLD = ('<script type="application/ld+json">\n'
          '{"@context":"https://schema.org","@graph":['
          '{"@type":"Organization","@id":"https://vrindavangreens.example/#org","name":"Vrindavan Greens",'
          '"url":"https://vrindavangreens.example/","logo":"https://vrindavangreens.example/assets/logo.png",'
          '"telephone":"+91-90516-22888","address":{"@type":"PostalAddress","streetAddress":"Alaipur, Madanpur",'
          '"addressLocality":"Kalyani","addressRegion":"Nadia, West Bengal","addressCountry":"IN"}},'
          '{"@type":"Place","name":"Vrindavan Greens","description":"A gated plotted community at Alaipur, '
          'Madanpur, near Kalyani, Nadia.","address":{"@type":"PostalAddress","streetAddress":"Alaipur, Madanpur",'
          '"addressLocality":"Kalyani","addressRegion":"Nadia, West Bengal","addressCountry":"IN"}}]}'
          '\n</script>')

PAGES = [
    dict(file="index.html", title="Vrindavan Greens \u2014 gated plotted community near Kalyani",
         desc="Own the land. Build the home. 166 plots, 2 minutes from Madanpur Station, 15 minutes from Kalyani.",
         content=rewrite(hero + sections["idea"] + explore_section),
         js=[]),
    dict(file="location.html", title="Location \u2014 Vrindavan Greens, Madanpur near Kalyani",
         desc="Two minutes from Madanpur Station, fifteen from Kalyani. Everything a growing family needs, within fifteen minutes.",
         content=rewrite(pagebar("Location") + sections["location"]), js=[]),
    dict(file="plots.html", title="Choose a plot \u2014 Vrindavan Greens site plan",
         desc="An interactive site plan of all 166 plots at Vrindavan Greens. Filter by phase and size, and tap any plot for details.",
         content=rewrite(pagebar("Choose a plot") + sections["plots"]), js=["DATA_MAP", "DEEPLINK"]),
    dict(file="plans.html", title="Home plans \u2014 Vrindavan Greens",
         desc="Home plans for 1.5 to 5+ katha plots, plus an interactive configurator to sketch your own layout.",
         content=rewrite(pagebar("Home plans") + sections["plans"]), js=["CONFIG"]),
    dict(file="pricing.html", title="Pricing \u2014 Vrindavan Greens",
         desc="Indicative starting price, a clear payment schedule and an EMI calculator for a plot purchase loan.",
         content=rewrite(pagebar("Pricing") + sections["pricing"]), js=["EMI"]),
    dict(file="amenities.html", title="Amenities \u2014 Vrindavan Greens",
         desc="A temple at the centre, a maidan for the evenings, a clubhouse, gym, pool and pond area \u2014 all looked after for you.",
         content=rewrite(pagebar("Amenities") + sections["club"]), js=[]),
    dict(file="why.html", title="Why here \u2014 Vrindavan Greens",
         desc="In Nadia, Vrindavan came to us. The soil where Bengal learned to sing Krishna's name.",
         content=rewrite(pagebar("Why here") + sections["why"]), js=[]),
    dict(file="tour.html", title="Walk the site \u2014 Vrindavan Greens",
         desc="A 360-degree walk through the layout and a gallery of the site and homes at Vrindavan Greens.",
         content=rewrite(pagebar("Walk the site") + sections["tour"]), js=["TOUR"]),
    dict(file="stories.html", title="Family stories \u2014 Vrindavan Greens",
         desc="What early families say about buying a plot and building a home at Vrindavan Greens.",
         content=rewrite(pagebar("Family stories") + sections["stories"]), js=[]),
    dict(file="loan.html", title="Loan support \u2014 Vrindavan Greens",
         desc="Plot purchase loans and construction-linked loans, plus help with the paperwork at Vrindavan Greens.",
         content=rewrite(pagebar("Loan support") + sections["loan"]), js=[]),
    dict(file="faq.html", title="FAQ \u2014 Vrindavan Greens",
         desc="Approvals, registration, timelines, maintenance and everything else buyers ask about Vrindavan Greens.",
         content=rewrite(pagebar("Questions") + sections["faq"]), js=[]),
    dict(file="contact.html", title="Contact \u2014 Vrindavan Greens",
         desc="Book a site visit, arrange a pick-up from Madanpur or Kalyani, or call the Vrindavan Greens sales desk.",
         content=rewrite(pagebar("Contact") + sections["contact"] + sections["trust"]), js=["REGISTER", "BROCHURE"]),
]

SCRIPT_MAP = {
    "DATA_MAP": data_map,
    "DEEPLINK": ext["deep-linkable plots, sharing, live holds"],
    "CONFIG": ext["interactive home configurator"],
    "EMI": ext["EMI calculator"],
    "TOUR": ext["virtual tour (on demand)"],
    "REGISTER": register,
    "BROCHURE": ext["brochure (lead capture)"],
}

PAGE_TPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<meta name="description" content="__DESC__">
<meta name="theme-color" content="#0F3524">
<link rel="canonical" href="__URL__">
<link rel="icon" type="image/svg+xml" href="assets/favicon.svg">
<link rel="apple-touch-icon" href="assets/icon-192.png">
<link rel="manifest" href="manifest.webmanifest">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Vrindavan Greens">
<meta property="og:title" content="__TITLE__">
<meta property="og:description" content="__DESC__">
<meta property="og:url" content="__URL__">
<meta property="og:image" content="https://vrindavangreens.example/assets/og-image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="en_IN">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="__TITLE__">
<meta name="twitter:description" content="__DESC__">
<meta name="twitter:image" content="https://vrindavangreens.example/assets/og-image.jpg">
<!-- VG:EDIT Google Search Console: paste your token and uncomment
<meta name="google-site-verification" content="REPLACE_WITH_GSC_TOKEN">
-->
__JSONLD__
<style>
__CSS__
</style>
<style>
__EXTRA_CSS__
</style>
</head>
<body>
__NAV__
__AUDIO__
__CONTENT__
__ACTIONBAR__
__WA__
__FOOTER__
<script>
__AUDIO_JS__
</script>
__PAGEJS__
</body></html>
"""

BASE = "https://vrindavangreens.example/"

for p in PAGES:
    js = "\n".join("<script>\n%s\n</script>" % SCRIPT_MAP[k] for k in p["js"])
    out = (PAGE_TPL
           .replace("__TITLE__", _html.escape(p["title"]))
           .replace("__DESC__", _html.escape(p["desc"], quote=True))
           .replace("__URL__", BASE + ("" if p["file"] == "index.html" else p["file"]))
           .replace("__CSS__", css)
           .replace("__EXTRA_CSS__", EXTRA_CSS)
           .replace("__JSONLD__", JSONLD)
           .replace("__NAV__", build_nav(p["file"]))
           .replace("__AUDIO__", sound_markup)
           .replace("__CONTENT__", p["content"])
           .replace("__ACTIONBAR__", actionbar)
           .replace("__WA__", wa_float)
           .replace("__FOOTER__", build_footer())
           .replace("__AUDIO_JS__", s1)
           .replace("__PAGEJS__", js))
    open(p["file"], "w", encoding="utf-8").write(out)
    print("wrote %-16s %7d bytes  scripts=%s" % (p["file"], len(out), p["js"] or "-"))
print("available plots:", len(avail), "of", len(plots), " total katha:", total_katha)
