use serde::Deserialize;
use std::borrow::Cow;
use std::collections::HashMap;
use std::io::{self, BufRead, BufReader, Write};
use std::fs::File;

#[derive(Deserialize)]
struct Header { rates: HashMap<String, i64> }
#[derive(Deserialize)]
struct Meta<'a> { #[serde(borrow)] channel: Cow<'a, str> }
#[derive(Deserialize)]
struct Transaction<'a> {
    #[serde(borrow)] account: Cow<'a, str>,
    #[serde(rename = "type", borrow)] kind: Cow<'a, str>,
    #[serde(borrow)] amount: Cow<'a, str>,
    #[serde(borrow)] currency: Cow<'a, str>,
    tags: Vec<String>,
    #[serde(borrow)] meta: Meta<'a>,
}

fn main() {
    let path = std::env::args_os().nth(1).expect("input path");
    let mut input = BufReader::with_capacity(1024 * 1024, File::open(path).unwrap());
    let mut line = Vec::with_capacity(1024);
    input.read_until(b'\n', &mut line).unwrap();
    let header: Header = serde_json::from_slice(&line).unwrap();
    let mut accounts: HashMap<String, i128> = HashMap::new();
    let mut channels: HashMap<String, (u64, i128)> = HashMap::new();
    let (mut count, mut net) = (0u64, 0i128);
    loop {
        line.clear();
        if input.read_until(b'\n', &mut line).unwrap() == 0 { break; }
        let tx: Transaction = serde_json::from_slice(&line).unwrap();
        if tx.kind == "void" || tx.tags.iter().any(|tag| tag == "test") { continue; }
        let rate = header.rates[tx.currency.as_ref()] as i128;
        let mut whole = 0i128;
        let mut fraction = 0i128;
        let mut digits = 0;
        let mut decimal = false;
        for b in tx.amount.bytes().filter(|_| rate != 0) {
            if b == b'.' { decimal = true; }
            else if decimal { fraction = fraction * 10 + (b - b'0') as i128; digits += 1; }
            else { whole = whole * 10 + (b - b'0') as i128; }
        }
        let cents = whole * 100 + if digits == 1 { fraction * 10 } else { fraction };
        let mut value = (cents * rate).div_euclid(1_000_000);
        if tx.kind == "debit" { value = -value; }
        count += 1;
        net += value;
        if let Some(v) = accounts.get_mut(tx.account.as_ref()) { *v += value; }
        else { accounts.insert(tx.account.into_owned(), value); }
        if let Some(v) = channels.get_mut(tx.meta.channel.as_ref()) { v.0 += 1; v.1 += value; }
        else { channels.insert(tx.meta.channel.into_owned(), (1, value)); }
    }
    let mut out = io::BufWriter::new(io::stdout().lock());
    writeln!(out, "counted {count}\nnet {net}").unwrap();
    let mut channels: Vec<_> = channels.into_iter().collect();
    channels.sort_unstable_by(|a, b| a.0.cmp(&b.0));
    for (name, (n, value)) in channels { writeln!(out, "channel {name} {n} {value}").unwrap(); }
    let mut accounts: Vec<_> = accounts.into_iter().collect();
    accounts.sort_unstable_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0)));
    for (name, value) in accounts.into_iter().take(10) { writeln!(out, "account {name} {value}").unwrap(); }
}
