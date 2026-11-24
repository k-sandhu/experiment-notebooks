import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadConstraints;

import java.io.BufferedInputStream;
import java.io.BufferedWriter;
import java.io.FileInputStream;
import java.io.OutputStreamWriter;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Map;
import java.util.PriorityQueue;

public class Main {
    private static final BigInteger HUNDRED = BigInteger.valueOf(100);

    private static final class Rate {
        final long value;
        final BigInteger big;

        Rate(BigInteger value) {
            this.value = value.longValue();
            this.big = value.bitLength() <= 63 ? null : value;
        }
    }

    private static final class Amount {
        long value;
        BigInteger big;
    }

    private static final class Totals {
        long count;
        long net;
    }

    private static void readAmount(JsonParser parser, Amount amount) throws Exception {
        char[] chars = parser.getTextCharacters();
        int offset = parser.getTextOffset();
        int length = parser.getTextLength();
        int end = offset + length;

        long value = 0;
        int fractionalDigits = -1;
        amount.big = null;

        for (int i = offset; i < end; i++) {
            char c = chars[i];
            if (c == '.') {
                fractionalDigits = 0;
                continue;
            }

            int digit = c - '0';
            if (value > 922337203685477580L
                    || (value == 922337203685477580L && digit > 7)) {
                readBigAmount(chars, offset, length, amount);
                return;
            }

            value = value * 10 + digit;
            if (fractionalDigits >= 0) {
                fractionalDigits++;
            }
        }

        int multiplier = fractionalDigits < 0 ? 100
                : fractionalDigits == 1 ? 10 : 1;

        if (value > Long.MAX_VALUE / multiplier) {
            readBigAmount(chars, offset, length, amount);
        } else {
            amount.value = value * multiplier;
        }
    }

    private static void readBigAmount(
            char[] chars, int offset, int length, Amount amount) {
        String text = new String(chars, offset, length);
        int dot = text.indexOf('.');
        if (dot < 0) {
            amount.big = new BigInteger(text).multiply(HUNDRED);
        } else {
            BigInteger unscaled = new BigInteger(
                    text.substring(0, dot) + text.substring(dot + 1));
            amount.big = text.length() - dot - 1 == 1
                    ? unscaled.multiply(BigInteger.TEN) : unscaled;
        }
    }

    private static long convert(Amount amount, Rate rate) {
        long product;
        if (rate.big == null && rate.value == 0) {
            return 0;
        } else if (amount.big == null && rate.big == null) {
            product = amount.value * rate.value;
        } else {
            BigInteger units = amount.big == null
                    ? BigInteger.valueOf(amount.value) : amount.big;
            BigInteger multiplier = rate.big == null
                    ? BigInteger.valueOf(rate.value) : rate.big;
            product = units.multiply(multiplier).longValueExact();
        }
        return Math.floorDiv(product, 1_000_000L);
    }

    public static void main(String[] args) throws Exception {
        JsonFactory factory = JsonFactory.builder()
                .streamReadConstraints(StreamReadConstraints.builder()
                        .maxNestingDepth(Integer.MAX_VALUE)
                        .maxNumberLength(Integer.MAX_VALUE)
                        .maxStringLength(Integer.MAX_VALUE)
                        .maxNameLength(Integer.MAX_VALUE)
                        .build())
                .disable(JsonFactory.Feature.INTERN_FIELD_NAMES)
                .disable(JsonFactory.Feature.FAIL_ON_SYMBOL_HASH_OVERFLOW)
                .build();

        HashMap<String, Rate> rates = new HashMap<>();
        HashMap<String, Totals> channels = new HashMap<>();
        HashMap<String, Totals> accounts = new HashMap<>();

        long counted = 0;
        long net = 0;
        Amount amount = new Amount();

        try (JsonParser parser = factory.createParser(
                new BufferedInputStream(new FileInputStream(args[0]), 1 << 18))) {
            parser.nextToken();
            String field;
            while ((field = parser.nextFieldName()) != null) {
                parser.nextToken();
                if (field.equals("rates")) {
                    String currency;
                    while ((currency = parser.nextFieldName()) != null) {
                        parser.nextToken();
                        rates.put(currency, new Rate(parser.getBigIntegerValue()));
                    }
                } else {
                    parser.skipChildren();
                }
            }

            while (parser.nextToken() != null) {
                String account = null;
                String channel = null;
                Rate rate = null;
                boolean debit = false;
                boolean skipped = false;

                while ((field = parser.nextFieldName()) != null) {
                    parser.nextToken();

                    switch (field) {
                        case "account":
                            account = parser.getText();
                            break;
                        case "currency":
                            rate = rates.get(parser.getText());
                            break;
                        case "amount":
                            readAmount(parser, amount);
                            break;
                        case "type":
                            String type = parser.getText();
                            debit = type.equals("debit");
                            skipped = type.equals("void");
                            break;
                        case "tags":
                            while (parser.nextToken() != JsonToken.END_ARRAY) {
                                if (!skipped && parser.getText().equals("test")) {
                                    skipped = true;
                                }
                            }
                            break;
                        case "meta":
                            String metaField;
                            while ((metaField = parser.nextFieldName()) != null) {
                                parser.nextToken();
                                if (metaField.equals("channel")) {
                                    channel = parser.getText();
                                } else {
                                    parser.skipChildren();
                                }
                            }
                            break;
                        default:
                            parser.skipChildren();
                            break;
                    }

                    if (skipped) {
                        while (parser.nextFieldName() != null) {
                            parser.nextToken();
                            parser.skipChildren();
                        }
                        break;
                    }
                }

                if (skipped) {
                    continue;
                }

                long signed = convert(amount, rate);
                if (debit) {
                    signed = -signed;
                }

                counted++;
                net += signed;

                Totals channelTotals = channels.get(channel);
                if (channelTotals == null) {
                    channelTotals = new Totals();
                    channels.put(channel, channelTotals);
                }
                channelTotals.count++;
                channelTotals.net += signed;

                Totals accountTotals = accounts.get(account);
                if (accountTotals == null) {
                    accountTotals = new Totals();
                    accounts.put(account, accountTotals);
                }
                accountTotals.net += signed;
            }
        }

        Comparator<Map.Entry<String, Totals>> bestFirst = (a, b) -> {
            int comparison = Long.compare(b.getValue().net, a.getValue().net);
            return comparison != 0
                    ? comparison : a.getKey().compareTo(b.getKey());
        };

        PriorityQueue<Map.Entry<String, Totals>> top =
                new PriorityQueue<>(10, bestFirst.reversed());

        for (Map.Entry<String, Totals> entry : accounts.entrySet()) {
            if (top.size() < 10) {
                top.add(entry);
            } else if (bestFirst.compare(entry, top.peek()) < 0) {
                top.poll();
                top.add(entry);
            }
        }

        ArrayList<Map.Entry<String, Totals>> ranked = new ArrayList<>(top);
        ranked.sort(bestFirst);

        String[] channelNames = channels.keySet().toArray(new String[0]);
        Arrays.sort(channelNames);

        BufferedWriter output = new BufferedWriter(
                new OutputStreamWriter(System.out, StandardCharsets.UTF_8), 1 << 16);

        output.write("counted " + counted + "\n");
        output.write("net " + net + "\n");

        for (String name : channelNames) {
            Totals totals = channels.get(name);
            output.write("channel " + name + " " + totals.count + " " + totals.net + "\n");
        }

        for (Map.Entry<String, Totals> entry : ranked) {
            output.write("account " + entry.getKey() + " " + entry.getValue().net + "\n");
        }

        output.flush();
    }
}
