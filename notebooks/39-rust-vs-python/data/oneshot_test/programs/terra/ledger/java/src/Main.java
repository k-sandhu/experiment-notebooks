import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadConstraints;

import java.io.BufferedInputStream;
import java.io.FileInputStream;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Map;
import java.util.PriorityQueue;

public class Main {
    private static final BigInteger MILLION = BigInteger.valueOf(1_000_000);

    private static final class Total {
        long count;
        long net;
    }

    private static final class Account {
        final String name;
        long net;

        Account(String name) {
            this.name = name;
        }
    }

    private static BigInteger bigHundredths(String amount) {
        int dot = amount.indexOf('.');
        if (dot < 0) {
            return new BigInteger(amount).multiply(BigInteger.valueOf(100));
        }
        int decimals = amount.length() - dot - 1;
        BigInteger value = new BigInteger(
                amount.substring(0, dot) + amount.substring(dot + 1));
        return decimals == 1 ? value.multiply(BigInteger.TEN) : value;
    }

    public static void main(String[] args) throws Exception {
        JsonFactory factory = JsonFactory.builder()
                .streamReadConstraints(StreamReadConstraints.builder()
                        .maxNestingDepth(Integer.MAX_VALUE)
                        .maxStringLength(Integer.MAX_VALUE)
                        .maxNumberLength(Integer.MAX_VALUE)
                        .build())
                .build();

        Map<String, Long> rates = new HashMap<>();
        Map<String, Total> channels = new HashMap<>();
        Map<String, Account> accounts = new HashMap<>();
        long count = 0;
        long net = 0;

        try (BufferedInputStream in = new BufferedInputStream(
                     new FileInputStream(args[0]), 1 << 20);
             JsonParser parser = factory.createParser(in)) {

            if (parser.nextToken() == null) {
                return;
            }

            while (parser.nextToken() != JsonToken.END_OBJECT) {
                String field = parser.currentName();
                parser.nextToken();
                if ("rates".equals(field)) {
                    while (parser.nextToken() != JsonToken.END_OBJECT) {
                        String currency = parser.currentName();
                        parser.nextToken();
                        rates.put(currency, parser.getLongValue());
                    }
                } else {
                    parser.skipChildren();
                }
            }

            while (parser.nextToken() != null) {
                String accountName = null;
                String channelName = null;
                String currency = null;
                String type = null;
                long hundredths = 0;
                BigInteger bigAmount = null;
                boolean test = false;

                while (parser.nextToken() != JsonToken.END_OBJECT) {
                    String field = parser.currentName();
                    parser.nextToken();

                    switch (field) {
                        case "account":
                            accountName = parser.getText();
                            break;
                        case "currency":
                            currency = parser.getText();
                            break;
                        case "type":
                            type = parser.getText();
                            break;
                        case "amount": {
                            char[] chars = parser.getTextCharacters();
                            int offset = parser.getTextOffset();
                            int length = parser.getTextLength();
                            long value = 0;
                            int decimals = -1;
                            boolean overflow = false;

                            for (int i = 0; i < length; i++) {
                                char c = chars[offset + i];
                                if (c == '.') {
                                    decimals = 0;
                                } else {
                                    int digit = c - '0';
                                    if (!overflow) {
                                        if (value > (Long.MAX_VALUE - digit) / 10) {
                                            overflow = true;
                                        } else {
                                            value = value * 10 + digit;
                                        }
                                    }
                                    if (decimals >= 0) {
                                        decimals++;
                                    }
                                }
                            }

                            int factor = decimals < 0 ? 100 : decimals == 1 ? 10 : 1;
                            if (!overflow && value <= Long.MAX_VALUE / factor) {
                                hundredths = value * factor;
                                bigAmount = null;
                            } else {
                                bigAmount = bigHundredths(parser.getText());
                            }
                            break;
                        }
                        case "tags":
                            test = false;
                            while (parser.nextToken() != JsonToken.END_ARRAY) {
                                if ("test".equals(parser.getText())) {
                                    test = true;
                                }
                            }
                            break;
                        case "meta":
                            channelName = null;
                            while (parser.nextToken() != JsonToken.END_OBJECT) {
                                String metaField = parser.currentName();
                                parser.nextToken();
                                if ("channel".equals(metaField)) {
                                    channelName = parser.getText();
                                } else {
                                    parser.skipChildren();
                                }
                            }
                            break;
                        default:
                            parser.skipChildren();
                            break;
                    }
                }

                if (test || "void".equals(type)) {
                    continue;
                }

                long rate = rates.get(currency);
                long usd;
                if (bigAmount == null) {
                    usd = (hundredths * rate) / 1_000_000;
                } else {
                    usd = bigAmount.multiply(BigInteger.valueOf(rate))
                            .divide(MILLION).longValueExact();
                }
                long signed = "debit".equals(type) ? -usd : usd;

                count++;
                net += signed;

                Total channel = channels.get(channelName);
                if (channel == null) {
                    channel = new Total();
                    channels.put(channelName, channel);
                }
                channel.count++;
                channel.net += signed;

                Account account = accounts.get(accountName);
                if (account == null) {
                    account = new Account(accountName);
                    accounts.put(accountName, account);
                }
                account.net += signed;
            }
        }

        Comparator<Account> worstFirst = (a, b) -> {
            int byNet = Long.compare(a.net, b.net);
            return byNet != 0 ? byNet : b.name.compareTo(a.name);
        };

        PriorityQueue<Account> top = new PriorityQueue<>(11, worstFirst);
        for (Account account : accounts.values()) {
            if (top.size() < 10) {
                top.add(account);
            } else if (worstFirst.compare(account, top.peek()) > 0) {
                top.poll();
                top.add(account);
            }
        }

        ArrayList<String> channelNames = new ArrayList<>(channels.keySet());
        channelNames.sort(String::compareTo);
        ArrayList<Account> bestAccounts = new ArrayList<>(top);
        bestAccounts.sort(worstFirst.reversed());

        StringBuilder output = new StringBuilder();
        output.append("counted ").append(count).append('\n');
        output.append("net ").append(net).append('\n');
        for (String name : channelNames) {
            Total total = channels.get(name);
            output.append("channel ").append(name).append(' ')
                    .append(total.count).append(' ')
                    .append(total.net).append('\n');
        }
        for (Account account : bestAccounts) {
            output.append("account ").append(account.name).append(' ')
                    .append(account.net).append('\n');
        }
        System.out.print(output);
    }
}
