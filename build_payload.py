#!/usr/bin/env python3
import argparse, json, sys, re, subprocess
from datetime import datetime, timezone


def _num(s):
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip()
    if s == "":
        return None
    # keep digits, dot, minus
    s2 = re.sub(r'[^0-9.\-]', '', s)
    try:
        return float(s2)
    except Exception:
        return None


def _pplx_fetch(url, prompt):
    # Uses pplx CLI available in PATH; requires caller to supply pplx-sdk creds in environment.
    cmd = ["pplx", "content", "fetch", url, "--prompt", prompt]
    out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True)
    return out.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--crypto_mcap', default='')
    ap.add_argument('--btc_dom', default='')
    ap.add_argument('--eth_btc_ratio', default='')
    args = ap.parse_args()

    metrics = {}

    # RWA.xyz JSON
    try:
        rwa_json = _pplx_fetch(
            'https://app.rwa.xyz/',
            'Extract: total RWA value excluding stablecoins, tokenized US Treasuries AUM, BlackRock BUIDL AUM, tokenized commodities total, tokenized private credit total, tokenized real estate total, tokenized equities total. Return JSON {rwa_total, tokenized_treas, buidl_aum, rwa_commodities, tokenized_credit, tokenized_real_estate, tokenized_equities} with values in USD.'
        )
        d = json.loads(rwa_json)
        for k in ['rwa_total','tokenized_treas','buidl_aum','rwa_commodities','tokenized_credit','tokenized_real_estate','tokenized_equities']:
            v = _num(d.get(k))
            if v and v > 0:
                metrics[k] = v
    except Exception:
        pass

    # DeFiLlama TVL
    try:
        tvl_raw = _pplx_fetch('https://defillama.com', 'Extract total DeFi TVL in USD. Return just the number.')
        tvl = _num(tvl_raw)
        if tvl and tvl > 0:
            metrics['defi_tvl'] = tvl
    except Exception:
        pass

    # Fear & Greed
    try:
        fg_raw = _pplx_fetch('https://alternative.me/crypto/fear-and-greed-index/', 'Extract today fear and greed index value 0-100. Return just the number.')
        fg = _num(fg_raw)
        # omit corrupt 0
        if fg and fg > 0:
            metrics['fear_greed'] = fg
    except Exception:
        pass

    # Crypto global metrics (omit corrupt zeros)
    cm = _num(args.crypto_mcap)
    if cm and cm > 0:
        metrics['crypto_mcap'] = cm
    bd = _num(args.btc_dom)
    if bd and bd > 0:
        metrics['btc_dom'] = bd
    er = _num(args.eth_btc_ratio)
    if er and er > 0:
        metrics['eth_btc_ratio'] = er

    payload = {
        'metrics': metrics,
        'news': [],
        'alerts': [],
        'assets': [],
        'run_utc': datetime.now(timezone.utc).isoformat(timespec='seconds')
    }

    json.dump(payload, sys.stdout)


if __name__ == '__main__':
    main()
