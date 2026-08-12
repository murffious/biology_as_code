-- Biology as Code — property-graph schema.
--
-- The constitution is enforced here, not in application code. Three rules are
-- structural rather than conventional:
--
--   1. Node labels and relation types are closed sets. A relation outside the
--      RelationType ENUM cannot be written.
--   2. Gate and bound are separate node labels and can never be collapsed,
--      because they are different tables' worth of constraint.
--   3. An edge that asserts a magnitude and carries no evidence is rejected by
--      trigger. Empty beats fake, at the storage layer.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- nodes

CREATE TABLE IF NOT EXISTS node (
    id     TEXT PRIMARY KEY,
    label  TEXT NOT NULL CHECK (label IN (
        'Law',          -- LAW-001 … LAW-047, the register
        'System',       -- the seven functional systems
        'Organ',
        'Subsystem',
        'Nutrient',
        'Compound',     -- modifiers: phytate, ascorbate, tannin …
        'Food',
        'Outcome',      -- a health endpoint a claim reaches for
        'Claim',
        'Gate',         -- categorical: open or closed. never a magnitude.
        'Bound',        -- magnitude with units and a scoping condition
        'Source',
        'Contribution'
    )),
    name   TEXT NOT NULL,
    props  TEXT NOT NULL DEFAULT '{}'   -- JSON
);

CREATE INDEX IF NOT EXISTS idx_node_label ON node (label);

-- ---------------------------------------------------------------- edges

CREATE TABLE IF NOT EXISTS edge (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    src       TEXT NOT NULL REFERENCES node (id) ON DELETE CASCADE,
    dst       TEXT NOT NULL REFERENCES node (id) ON DELETE CASCADE,
    rel       TEXT NOT NULL CHECK (rel IN (
        -- closed biological RelationType ENUM (schemas/relation_enums.subset.json)
        'OPENS_GATE',
        'CLOSES_GATE',
        'EXPANDS_BOUND',
        'NARROWS_BOUND',
        'CONSERVES',
        'IDENTITY',
        'COMPETES_WITH',
        'PART_OF',
        'NEEDS_RESOLUTION',
        'MALFORMED_MECHANISM',
        -- structural edges. not biological assertions; carry no magnitude.
        'SEATED_IN',        -- Law     -> System
        'LOCATED_AT',       -- Law     -> Organ
        'HAS_GATE',         -- Law     -> Gate
        'HAS_BOUND',        -- Law     -> Bound
        'GOVERNS',          -- Law     -> Nutrient | Compound
        'CONTAINS',         -- Food    -> Nutrient | Compound
        'CLAIMS',           -- Food    -> Claim
        'TARGETS',          -- Claim   -> Outcome
        'RESOLVES_TO',      -- Claim   -> Law
        'EVIDENCED_BY',     -- Law | Claim -> Contribution
        'CITES',            -- Contribution -> Source
        'DRIVEN_BY'         -- Claim   -> Compound
    )),
    -- an edge asserting a magnitude must name the evidence that licenses it
    asserts_magnitude INTEGER NOT NULL DEFAULT 0 CHECK (asserts_magnitude IN (0, 1)),
    evidence  TEXT REFERENCES node (id),
    strength  INTEGER CHECK (strength IS NULL OR strength BETWEEN 0 AND 5),
    props     TEXT NOT NULL DEFAULT '{}',
    UNIQUE (src, dst, rel)
);

CREATE INDEX IF NOT EXISTS idx_edge_src ON edge (src, rel);
CREATE INDEX IF NOT EXISTS idx_edge_dst ON edge (dst, rel);
CREATE INDEX IF NOT EXISTS idx_edge_rel ON edge (rel);

-- Fail-closed: refuse an unsourced magnitude at write time.
CREATE TRIGGER IF NOT EXISTS trg_edge_magnitude_needs_evidence
BEFORE INSERT ON edge
FOR EACH ROW WHEN NEW.asserts_magnitude = 1 AND NEW.evidence IS NULL
BEGIN
    SELECT RAISE(ABORT, 'fail-closed: edge asserts a magnitude with no evidence node; attach a Contribution or leave the bound OPEN');
END;

-- Gate nodes are categorical. A gate carrying a numeric magnitude is the
-- gate/bound collapse the register exists to prevent.
CREATE TRIGGER IF NOT EXISTS trg_gate_is_categorical
BEFORE INSERT ON node
FOR EACH ROW WHEN NEW.label = 'Gate'
     AND json_extract(NEW.props, '$.magnitude') IS NOT NULL
BEGIN
    SELECT RAISE(ABORT, 'gate/bound collapse: a Gate may not carry a magnitude; split it into a Gate (categorical) and a Bound (magnitude)');
END;

-- ---------------------------------------------------------------- views

-- Every law with its seat, gate presence and executability.
CREATE VIEW IF NOT EXISTS v_law_card AS
SELECT
    n.id                                    AS law_id,
    n.name                                  AS statement,
    json_extract(n.props, '$.system')       AS system,
    json_extract(n.props, '$.organ')        AS organ,
    json_extract(n.props, '$.gate_present') AS gate_present,
    json_extract(n.props, '$.bound_text')   AS bound_text,
    json_extract(n.props, '$.executable')   AS executable,
    json_extract(n.props, '$.status')       AS status
FROM node n
WHERE n.label = 'Law';

-- Laws that assert a bound with no evidence attached anywhere.
CREATE VIEW IF NOT EXISTS v_unsourced_bounds AS
SELECT l.law_id, l.bound_text, l.system
FROM v_law_card l
WHERE l.bound_text IS NOT NULL
  AND l.bound_text <> ''
  AND NOT EXISTS (
      SELECT 1 FROM edge e
      WHERE e.src = l.law_id AND e.rel = 'EVIDENCED_BY'
  );

-- Evidence coverage per law.
CREATE VIEW IF NOT EXISTS v_law_evidence AS
SELECT
    l.law_id,
    COUNT(e.id)                AS contributions,
    COALESCE(MAX(e.strength), 0) AS best_strength
FROM v_law_card l
LEFT JOIN edge e ON e.src = l.law_id AND e.rel = 'EVIDENCED_BY'
GROUP BY l.law_id;
