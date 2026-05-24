//! dm-dump: walk an SS13 codebase's BYOND type tree and emit it as NDJSON.
//!
//! One JSON object per line, each shaped like:
//!     {"path":"/obj/test/widget", "parent":"/obj/test", "vars":[{"name":"charge","value":"0"}],
//!      "procs":[{"name":"zap"}], "file":"code/modules/test/widget.dm", "line":1}
//!
//! Built because upstream SpacemanDMM's published `dmm-tools` does not expose a
//! `dump-types` subcommand; this binary uses the same `dreammaker` parser crate
//! that powers dm-langserver / dmdoc / dmm-tools, then dumps the parsed tree.
//! See https://github.com/vg14-developers/ss13-mcp/issues/16.

extern crate dreammaker as dm;

use std::env;
use std::io::{self, BufWriter, Write};
use std::path::{Path, PathBuf};
use std::process::ExitCode;

use serde_json::{json, Value};

const USAGE: &str = "usage: dm-dump <path-to-ss13-checkout-or-dme>";

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();
    if args.len() == 2 && (args[1] == "--version" || args[1] == "-V") {
        println!("dm-dump {}", env!("CARGO_PKG_VERSION"));
        return ExitCode::SUCCESS;
    }
    if args.len() == 2 && (args[1] == "--help" || args[1] == "-h") {
        println!("{USAGE}");
        return ExitCode::SUCCESS;
    }
    if args.len() != 2 {
        eprintln!("{USAGE}");
        return ExitCode::from(2);
    }

    let target = PathBuf::from(&args[1]);
    let dme = match resolve_dme(&target) {
        Ok(p) => p,
        Err(e) => {
            eprintln!("dm-dump: {e}");
            return ExitCode::from(2);
        }
    };
    let root = dme.parent().unwrap_or(Path::new(".")).to_path_buf();

    let context = dm::Context::default();
    let pp = match dm::preprocessor::Preprocessor::new(&context, dme.clone()) {
        Ok(pp) => pp,
        Err(e) => {
            eprintln!("dm-dump: preprocessor failed on {}: {e}", dme.display());
            return ExitCode::from(1);
        }
    };
    let indents = dm::indents::IndentProcessor::new(&context, pp);
    let mut parser = dm::parser::Parser::new(&context, indents);
    parser.enable_procs();
    let tree = parser.parse_object_tree();

    let stdout = io::stdout().lock();
    let mut out = BufWriter::new(stdout);
    let mut io_err: Option<io::Error> = None;

    tree.root().recurse(&mut |ty| {
        if io_err.is_some() {
            return;
        }
        if let Err(e) = emit(&mut out, &context, &root, ty) {
            io_err = Some(e);
        }
    });

    if let Some(e) = io_err {
        eprintln!("dm-dump: write failed: {e}");
        return ExitCode::from(1);
    }
    if let Err(e) = out.flush() {
        eprintln!("dm-dump: flush failed: {e}");
        return ExitCode::from(1);
    }
    ExitCode::SUCCESS
}

fn resolve_dme(target: &Path) -> Result<PathBuf, String> {
    if !target.exists() {
        return Err(format!("path does not exist: {}", target.display()));
    }
    if target.is_file()
        && target.extension().and_then(|s| s.to_str()) == Some("dme")
    {
        return Ok(target.to_path_buf());
    }
    if target.is_dir() {
        let mut found: Option<PathBuf> = None;
        for entry in std::fs::read_dir(target)
            .map_err(|e| format!("read_dir {}: {e}", target.display()))?
            .flatten()
        {
            let p = entry.path();
            if p.is_file()
                && p.extension().and_then(|s| s.to_str()) == Some("dme")
            {
                if found.is_some() {
                    return Err(format!(
                        "multiple .dme files in {}; pass the specific one",
                        target.display()
                    ));
                }
                found = Some(p);
            }
        }
        return found.ok_or_else(|| {
            format!("no .dme file found at top level of {}", target.display())
        });
    }
    Err(format!("not a .dme file or directory: {}", target.display()))
}

fn emit<W: Write>(
    out: &mut W,
    context: &dm::Context,
    root: &Path,
    ty: dm::objtree::TypeRef<'_>,
) -> io::Result<()> {
    let path = ty.path.clone();
    let parent: Option<String> = ty.parent_type().map(|p| p.path.clone());

    let vars: Vec<Value> = ty
        .vars
        .iter()
        .map(|(name, var)| {
            let value: Option<String> = var
                .value
                .constant
                .as_ref()
                .map(|c| c.to_string())
                .or_else(|| {
                    var.value
                        .expression
                        .as_ref()
                        .map(|e| format!("{e:?}"))
                });
            json!({"name": name, "value": value})
        })
        .collect();

    let procs: Vec<Value> = ty
        .procs
        .keys()
        .map(|name| json!({"name": name}))
        .collect();

    let loc = ty.location;
    let file_path = context.file_path(loc.file);
    let path_ref: &Path = &file_path;
    let rel = path_ref
        .strip_prefix(root)
        .unwrap_or(path_ref)
        .to_string_lossy()
        .replace('\\', "/");

    let record = json!({
        "path": path,
        "parent": parent,
        "vars": vars,
        "procs": procs,
        "file": rel,
        "line": loc.line,
    });
    writeln!(out, "{record}")
}
