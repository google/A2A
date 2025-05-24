import { parseArgs as nodeParseArgs } from "util";
import { sep } from "path";

export interface ArgvOption {
  type: "string" | "boolean";
  short: string;
}

export type ArgvOptions = {
  [key: string]: ArgvOption;
};

type Params = {
  args: string[],
  options: ArgvOptions
}

export function parseArgs({args, options}: Params) {
  const optionShortToKey = Object.fromEntries(
    Object.entries(options).map(([key, opt]) => [opt.short, key])
  );

  const normalized = [];
  for (let i = 0; i < args.length; i++) {
    const current = args[i];
    const next = args[i + 1];

    // Check if next is a negative number (int or float)
    const isNegativeNumber = /^-\d+(\.\d+)?$/.test(next);

    // If current is a short option like -x and next is a negative number, combine
    if (/^-[a-zA-Z]$/.test(current) && isNegativeNumber ) {
      const key = current[1];
      const optionName = optionShortToKey[key];
      if (options[optionName]?.type === "string") {
        normalized.push(`${current}=${next}`);
        i++; // skip next, already used
        continue;
      }
    }
    normalized.push(current);
  }

  return nodeParseArgs({ args: normalized, options });
}

export function argvToCommand( argv: string[] ) {
  const program = argv[0].split( sep ).at(-1);
  const script = argv[1].split( sep ).slice(-2).join( sep );

  return `${program} ${script}`;
}
