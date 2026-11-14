use serde::Deserialize;
use std::borrow::Cow;
use std::collections::HashMap;
use std::env;
use std::fs::File;
use std::io::{self, BufRead, BufReader, BufWriter, Write};

#[derive(Deserialize)]
struct Header {
    rates: HashMap<String, i128>,
}

struct Parser<'a> {
    data: &'a [u8],
    pos: usize,
}

impl<'a> Parser<'a> {
    #[inline]
    fn whitespace(&mut self) {
        while self.pos < self.data.len()
            && matches!(self.data[self.pos], b' ' | b'\t' | b'\r' | b'\n')
        {
            self.pos += 1;
        }
    }

    #[inline]
    fn consume(&mut self, byte: u8) {
        self.whitespace();
        debug_assert_eq!(self.data[self.pos], byte);
        self.pos += 1;
    }

    fn string(&mut self) -> Cow<'a, str> {
        self.whitespace();
        let start = self.pos;
        debug_assert_eq!(self.data[start], b'"');
        self.pos += 1;
        let content_start = self.pos;
        let mut escaped = false;

        loop {
            match self.data[self.pos] {
                b'"' => {
                    let end = self.pos;
                    self.pos += 1;
                    if escaped {
                        return Cow::Owned(
                            serde_json::from_slice::<String>(&self.data[start..self.pos]).unwrap(),
                        );
                    }
                    return Cow::Borrowed(
                        std::str::from_utf8(&self.data[content_start..end]).unwrap(),
                    );
                }
                b'\\' => {
                    escaped = true;
                    self.pos += 2;
                }
                _ => self.pos += 1,
            }
        }
    }

    #[inline]
    fn skip_string(&mut self) {
        self.pos += 1;
        loop {
            match self.data[self.pos] {
                b'"' => {
                    self.pos += 1;
                    return;
                }
                b'\\' => self.pos += 2,
                _ => self.pos += 1,
            }
        }
    }

    fn skip_value(&mut self) {
        self.whitespace();
        match self.data[self.pos] {
            b'"' => self.skip_string(),
            b'{' | b'[' => {
                self.pos += 1;
                let mut depth = 1usize;
                while depth != 0 {
                    match self.data[self.pos] {
                        b'"' => self.skip_string(),
                        b'{' | b'[' => {
                            depth += 1;
                            self.pos += 1;
                        }
                        b'}' | b']' => {
                            depth -= 1;
                            self.pos += 1;
                        }
                        _ => self.pos += 1,
                    }
                }
            }
            _ => {
                while self.pos < self.data.len()
                    && !matches!(
                        self.data[self.pos],
                        b',' | b'}' | b']' | b' ' | b'\t' | b'\r' | b'\n'
                    )
                {
                    self.pos += 1;
                }
            }
        }
    }

    fn tags_contain_test(&mut self) -> bool {
        self.consume(b'[');
        loop {
            self.whitespace();
            if self.data[self.pos] == b']' {
                self.pos += 1;
                return false;
            }
            if self.string() == "test" {
                return true;
            }
            self.whitespace();
            if self.data[self.pos] == b',' {
                self.pos += 1;
            } else {
                self.consume(b']');
                return false;
            }
        }
    }

    fn channel(&mut self) -> Cow<'a, str> {
        self.consume(b'{');
        let mut channel = Cow::Borrowed("");
        loop {
            self.whitespace();
            if self.data[self.pos] == b'}' {
                self.pos += 1;
                return channel;
            }
            let key = self.string();
            self.consume(b':');
            if key == "channel" {
                channel = self.string();
            } else {
                self.skip_value();
            }
            self.whitespace();
            if self.data[self.pos] == b',' {
                self.pos += 1;
            } else {
                self.consume(b'}');
                return channel;
            }
        }
    }
}

struct Transaction<'a> {
    account: Cow<'a, str>,
    kind: Cow<'a, str>,
    amount: Cow<'a, str>,
    currency: Cow<'a, str>,
    channel: Cow<'a, str>,
}

fn parse_transaction(data: &[u8]) -> Option<Transaction<'_>> {
    let mut parser = Parser { data, pos: 0 };
    let mut transaction = Transaction {
        account: Cow::Borrowed(""),
        kind: Cow::Borrowed(""),
        amount: Cow::Borrowed(""),
        currency: Cow::Borrowed(""),
        channel: Cow::Borrowed(""),
    };

    parser.consume(b'{');
    loop {
        parser.whitespace();
        if parser.data[parser.pos] == b'}' {
            break;
        }

        let key = parser.string();
        parser.consume(b':');
        match key.as_ref() {
            "account" => transaction.account = parser.string(),
            "type" => {
                transaction.kind = parser.string();
                if transaction.kind == "void" {
                    return None;
                }
            }
            "amount" => transaction.amount = parser.string(),
            "currency" => transaction.currency = parser.string(),
            "tags" => {
                if parser.tags_contain_test() {
                    return None;
                }
            }
            "meta" => transaction.channel = parser.channel(),
            _ => parser.skip_value(),
        }

        parser.whitespace();
        if parser.data[parser.pos] == b',' {
            parser.pos += 1;
        } else {
            break;
        }
    }

    Some(transaction)
}

fn hundredths(amount: &str) -> i128 {
    let bytes = amount.as_bytes();
    let mut value = 0i128;
    let mut pos = 0;

    while pos < bytes.len() && bytes[pos] != b'.' {
        value = value * 10 + i128::from(bytes[pos] - b'0');
        pos += 1;
    }

    value *= 100;
    if pos < bytes.len() {
        pos += 1;
        value += i128::from(bytes[pos] - b'0') * 10;
        pos += 1;
        if pos < bytes.len() {
            value += i128::from(bytes[pos] - b'0');
        }
    }
    value
}

fn main() {
    let path = env::args_os().nth(1).expect("missing input path");
    let file = File::open(path).expect("cannot open input");
    let mut reader = BufReader::with_capacity(1024 * 1024, file);
    let mut line = Vec::with_capacity(4096);

    reader.read_until(b'\n', &mut line).unwrap();
    let header: Header = serde_json::from_slice(&line).unwrap();

    let mut accounts: HashMap<String, i128> = HashMap::new();
    let mut channels: HashMap<String, (u64, i128)> = HashMap::new();
    let mut count = 0u64;
    let mut net = 0i128;

    loop {
        line.clear();
        if reader.read_until(b'\n', &mut line).unwrap() == 0 {
            break;
        }

        let Some(transaction) = parse_transaction(&line) else {
            continue;
        };

        let rate = header.rates[transaction.currency.as_ref()];
        let usd = if rate == 0 {
            0
        } else {
            (hundredths(&transaction.amount) * rate).div_euclid(1_000_000)
        };
        let signed = if transaction.kind == "debit" {
            -usd
        } else {
            usd
        };

        count += 1;
        net += signed;

        if let Some(total) = accounts.get_mut(transaction.account.as_ref()) {
            *total += signed;
        } else {
            accounts.insert(transaction.account.into_owned(), signed);
        }

        if let Some(total) = channels.get_mut(transaction.channel.as_ref()) {
            total.0 += 1;
            total.1 += signed;
        } else {
            channels.insert(transaction.channel.into_owned(), (1, signed));
        }
    }

    let mut channel_rows: Vec<_> = channels.into_iter().collect();
    channel_rows.sort_unstable_by(|a, b| a.0.cmp(&b.0));

    let mut account_rows: Vec<_> = accounts.into_iter().collect();
    if account_rows.len() > 10 {
        account_rows.select_nth_unstable_by(10, |a, b| {
            b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0))
        });
        account_rows.truncate(10);
    }
    account_rows.sort_unstable_by(|a, b| {
        b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0))
    });

    let stdout = io::stdout();
    let mut out = BufWriter::new(stdout.lock());
    writeln!(out, "counted {count}").unwrap();
    writeln!(out, "net {net}").unwrap();
    for (name, (channel_count, channel_net)) in channel_rows {
        writeln!(out, "channel {name} {channel_count} {channel_net}").unwrap();
    }
    for (account, total) in account_rows {
        writeln!(out, "account {account} {total}").unwrap();
    }
}
