import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;

import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class Main {
    static final class Rate {
        String name;
        long value;
    }

    static final class Tx {
        String account;
        String type;
        long hundredths;
        String currency;
        boolean testTag;
        String channel;
    }

    static final class Ch {
        long count;
        long net;
    }

    static final class Ac {
        String id;
        long net;
    }

    // Append a signed long to a StringBuilder.
    static void appendLong(StringBuilder sb, long v) {
        if (v == Long.MIN_VALUE) {
            sb.append("-9223372036854775808");
            return;
        }
        if (v < 0) {
            sb.append('-');
            v = -v;
        }
        if (v == 0) {
            sb.append('0');
            return;
        }
        char[] buf = new char[20];
        int i = buf.length;
        while (v > 0) {
            buf[--i] = (char) ('0' + (v % 10));
            v /= 10;
        }
        sb.append(buf, i, buf.length - i);
    }

    // Convert amount string "12", "12.5", "12.05" to integer hundredths.
    static long parseAmount(String s) {
        int dot = s.indexOf('.');
        if (dot < 0) {
            return Long.parseLong(s) * 100;
        }
        long h = Long.parseLong(s.substring(0, dot));
        int fracLen = s.length() - dot - 1;
        long f = 0;
        for (int i = dot + 1; i < s.length(); i++) {
            f = f * 10 + (s.charAt(i) - '0');
        }
        if (fracLen == 1) {
            return h * 100 + f * 10;
        }
        return h * 100 + f;
    }

    public static void main(String[] args) throws Exception {
        byte[] data = Files.readAllBytes(Paths.get(args[0]));
        int n = data.length;

        // Locate end of first line (rates line).
        int firstNewline = -1;
        for (int i = 0; i < n; i++) {
            if (data[i] == '\n') {
                firstNewline = i;
                break;
            }
        }
        if (firstNewline < 0) firstNewline = n;

        // Parse rates from first line using Jackson streaming.
        JsonFactory factory = new JsonFactory();
        Map<String, Long> rateMap = new HashMap<>();
        String firstLine = new String(data, 0, firstNewline, StandardCharsets.UTF_8);
        try (JsonParser p = factory.createParser(firstLine)) {
            p.nextToken(); // START_OBJECT
            while (p.nextToken() != JsonToken.END_OBJECT) {
                String name = p.getCurrentName();
                p.nextToken(); // value token
                if ("rates".equals(name)) {
                    // value is START_OBJECT
                    while (p.nextToken() != JsonToken.END_OBJECT) {
                        String cname = p.getCurrentName();
                        p.nextToken(); // VALUE_NUMBER_INT
                        rateMap.put(cname, p.getLongValue());
                    }
                } else {
                    if (p.getCurrentToken() == JsonToken.START_OBJECT
                            || p.getCurrentToken() == JsonToken.START_ARRAY) {
                        p.skipChildren();
                    }
                }
            }
        }

        Map<String, Long> accounts = new HashMap<>();
        Map<String, Ch> channels = new HashMap<>();
        long counted = 0;
        long net = 0;

        int start = firstNewline + 1;
        while (start < n) {
            int end = start;
            while (end < n && data[end] != '\n') end++;
            // line is data[start..end)
            String line = new String(data, start, end - start, StandardCharsets.UTF_8);
            start = (end < n) ? end + 1 : end;

            Tx tx = new Tx();
            try (JsonParser p = factory.createParser(line)) {
                p.nextToken(); // START_OBJECT
                while (p.nextToken() != JsonToken.END_OBJECT) {
                    String name = p.getCurrentName();
                    p.nextToken(); // value token
                    JsonToken vt = p.getCurrentToken();
                    switch (name) {
                        case "account":
                            tx.account = p.getText();
                            break;
                        case "type":
                            tx.type = p.getText();
                            break;
                        case "amount":
                            tx.hundredths = parseAmount(p.getText());
                            break;
                        case "currency":
                            tx.currency = p.getText();
                            break;
                        case "tags":
                            // vt == START_ARRAY
                            while (p.nextToken() != JsonToken.END_ARRAY) {
                                if (p.getCurrentToken() == JsonToken.VALUE_STRING
                                        && "test".equals(p.getText())) {
                                    tx.testTag = true;
                                } else if (p.getCurrentToken() == JsonToken.START_OBJECT) {
                                    p.skipChildren();
                                }
                            }
                            break;
                        case "meta":
                            // vt == START_OBJECT
                            while (p.nextToken() != JsonToken.END_OBJECT) {
                                String mname = p.getCurrentName();
                                p.nextToken(); // value
                                if ("channel".equals(mname)) {
                                    tx.channel = p.getText();
                                } else if (p.getCurrentToken() == JsonToken.START_OBJECT
                                        || p.getCurrentToken() == JsonToken.START_ARRAY) {
                                    p.skipChildren();
                                }
                            }
                            break;
                        default:
                            if (vt == JsonToken.START_OBJECT || vt == JsonToken.START_ARRAY) {
                                p.skipChildren();
                            }
                            break;
                    }
                }
            }

            if (tx.type != null && !tx.type.equals("void") && !tx.testTag) {
                Long rate = rateMap.get(tx.currency);
                if (rate == null) rate = 0L;
                long usd = (tx.hundredths * rate) / 1000000L;
                long val = (tx.type.equals("credit") || tx.type.equals("refund")) ? usd : -usd;
                counted++;
                net += val;
                Ch c = channels.computeIfAbsent(tx.channel, k -> new Ch());
                c.count++;
                c.net += val;
                accounts.merge(tx.account, val, Long::sum);
            }
        }

        StringBuilder sb = new StringBuilder();
        sb.append("counted ");
        appendLong(sb, counted);
        sb.append('\n');
        sb.append("net ");
        appendLong(sb, net);
        sb.append('\n');

        // Channels sorted by name ascending.
        List<Map.Entry<String, Ch>> chList = new ArrayList<>(channels.entrySet());
        chList.sort((a, b) -> a.getKey().compareTo(b.getKey()));
        for (Map.Entry<String, Ch> e : chList) {
            sb.append("channel ");
            sb.append(e.getKey());
            sb.append(' ');
            appendLong(sb, e.getValue().count);
            sb.append(' ');
            appendLong(sb, e.getValue().net);
            sb.append('\n');
        }

        // Top 10 accounts: net desc, id asc.
        List<Map.Entry<String, Long>> acList = new ArrayList<>(accounts.entrySet());
        acList.sort((a, b) -> {
            long cmp = Long.compare(b.getValue(), a.getValue());
            if (cmp != 0) return (int) cmp;
            return a.getKey().compareTo(b.getKey());
        });
        int m = Math.min(acList.size(), 10);
        for (int i = 0; i < m; i++) {
            sb.append("account ");
            sb.append(acList.get(i).getKey());
            sb.append(' ');
            appendLong(sb, acList.get(i).getValue());
            sb.append('\n');
        }

        System.out.print(sb);
    }
}
