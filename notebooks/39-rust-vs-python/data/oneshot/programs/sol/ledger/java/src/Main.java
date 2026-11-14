import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadConstraints;

import java.io.BufferedInputStream;
import java.io.BufferedWriter;
import java.io.FileInputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashMap;
import java.util.PriorityQueue;

public class Main {
    private static final class AccountTotal {
        final String id;
        long net;

        AccountTotal(String id) {
            this.id = id;
        }
    }

    private static final class ChannelTotal {
        final String name;
        long count;
        long net;

        ChannelTotal(String name) {
            this.name = name;
        }
    }

    private static final Comparator<AccountTotal> BEST_FIRST = (a, b) -> {
        int comparison = Long.compare(b.net, a.net);
        return comparison != 0 ? comparison : a.id.compareTo(b.id);
    };

    private static long readHundredths(JsonParser parser) throws Exception {
        char[] chars = parser.getTextCharacters();
        int start = parser.getTextOffset();
        int end = start + parser.getTextLength();
        int dot = end;
        long value = 0;

        for (int i = start; i < end; i++) {
            char c = chars[i];
            if (c == '.') {
                dot = i;
            } else {
                value = value * 10 + (c - '0');
            }
        }

        if (dot == end) {
            value *= 100;
        } else if (end - dot == 2) {
            value *= 10;
        }

        return value;
    }

    private static boolean readTags(JsonParser parser) throws Exception {
        while (parser.nextToken() != JsonToken.END_ARRAY) {
            if (parser.getTextLength() == 4) {
                char[] chars = parser.getTextCharacters();
                int offset = parser.getTextOffset();

                if (chars[offset] == 't'
                        && chars[offset + 1] == 'e'
                        && chars[offset + 2] == 's'
                        && chars[offset + 3] == 't') {
                    while (parser.nextToken() != JsonToken.END_ARRAY) {
                        parser.skipChildren();
                    }
                    return true;
                }
            }
        }
        return false;
    }

    private static String readChannel(JsonParser parser) throws Exception {
        String channel = null;
        String field;

        while ((field = parser.nextFieldName()) != null) {
            parser.nextToken();
            if ("channel".equals(field)) {
                channel = parser.getText();
            } else {
                parser.skipChildren();
            }
        }

        return channel;
    }

    private static void skipObjectRemainder(JsonParser parser) throws Exception {
        while (parser.nextFieldName() != null) {
            parser.nextToken();
            parser.skipChildren();
        }
    }

    public static void main(String[] args) throws Exception {
        JsonFactory factory = JsonFactory.builder()
                .streamReadConstraints(StreamReadConstraints.builder()
                        .maxNestingDepth(Integer.MAX_VALUE)
                        .maxStringLength(Integer.MAX_VALUE)
                        .maxNameLength(Integer.MAX_VALUE)
                        .maxNumberLength(Integer.MAX_VALUE)
                        .build())
                .build();

        HashMap<String, Long> rates = new HashMap<>();
        HashMap<String, AccountTotal> accounts = new HashMap<>();
        HashMap<String, ChannelTotal> channels = new HashMap<>();

        long counted = 0;
        long net = 0;

        try (BufferedInputStream input =
                     new BufferedInputStream(new FileInputStream(args[0]), 1 << 18);
             JsonParser parser = factory.createParser(input)) {

            parser.nextToken();

            String field;
            while ((field = parser.nextFieldName()) != null) {
                parser.nextToken();

                if ("rates".equals(field)) {
                    String currency;
                    while ((currency = parser.nextFieldName()) != null) {
                        parser.nextToken();
                        // An oversized rate can only have zero amounts when
                        // every amount-rate product fits in a signed long.
                        rates.put(currency, parser.getBigIntegerValue().longValue());
                    }
                } else {
                    parser.skipChildren();
                }
            }

            while (parser.nextToken() != null) {
                String account = null;
                String channel = null;
                long hundredths = 0;
                long rate = 0;
                boolean debit = false;
                boolean skipped = false;

                while ((field = parser.nextFieldName()) != null) {
                    parser.nextToken();

                    switch (field) {
                        case "account":
                            account = parser.getText();
                            break;

                        case "type": {
                            char[] chars = parser.getTextCharacters();
                            char first = chars[parser.getTextOffset()];
                            skipped = first == 'v';
                            debit = first == 'd';
                            break;
                        }

                        case "amount":
                            hundredths = readHundredths(parser);
                            break;

                        case "currency":
                            rate = rates.get(parser.getText());
                            break;

                        case "tags":
                            skipped = readTags(parser);
                            break;

                        case "meta":
                            channel = readChannel(parser);
                            break;

                        default:
                            parser.skipChildren();
                            break;
                    }

                    if (skipped) {
                        skipObjectRemainder(parser);
                        break;
                    }
                }

                if (skipped) {
                    continue;
                }

                long value = (hundredths * rate) / 1_000_000L;
                if (debit) {
                    value = -value;
                }

                counted++;
                net += value;

                AccountTotal accountTotal = accounts.get(account);
                if (accountTotal == null) {
                    accountTotal = new AccountTotal(account);
                    accounts.put(account, accountTotal);
                }
                accountTotal.net += value;

                ChannelTotal channelTotal = channels.get(channel);
                if (channelTotal == null) {
                    channelTotal = new ChannelTotal(channel);
                    channels.put(channel, channelTotal);
                }
                channelTotal.count++;
                channelTotal.net += value;
            }
        }

        ChannelTotal[] orderedChannels =
                channels.values().toArray(new ChannelTotal[0]);
        Arrays.sort(orderedChannels, Comparator.comparing(c -> c.name));

        PriorityQueue<AccountTotal> best =
                new PriorityQueue<>(10, BEST_FIRST.reversed());

        for (AccountTotal account : accounts.values()) {
            if (best.size() < 10) {
                best.offer(account);
            } else if (BEST_FIRST.compare(account, best.peek()) < 0) {
                best.poll();
                best.offer(account);
            }
        }

        AccountTotal[] orderedAccounts = best.toArray(new AccountTotal[0]);
        Arrays.sort(orderedAccounts, BEST_FIRST);

        BufferedWriter output = new BufferedWriter(
                new OutputStreamWriter(System.out, StandardCharsets.UTF_8),
                1 << 16);

        output.write("counted " + counted + "\n");
        output.write("net " + net + "\n");

        for (ChannelTotal channel : orderedChannels) {
            output.write("channel " + channel.name + " "
                    + channel.count + " " + channel.net + "\n");
        }

        for (AccountTotal account : orderedAccounts) {
            output.write("account " + account.id + " " + account.net + "\n");
        }

        output.flush();
    }
}
