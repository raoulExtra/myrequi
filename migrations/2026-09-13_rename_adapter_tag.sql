-- Rename the generic adapter tag and assign it to the Telegram messenger adapter.
DELETE FROM object_epistemic_tags WHERE tag_key='integration:adapter';
DELETE FROM epistemic_tags WHERE tag_key='integration:adapter';

INSERT OR IGNORE INTO epistemic_tags(tag_key, label, description)
VALUES (
    'kind:messenger-adapter',
    'Messenger adapter',
    'Identifies an extension that delivers messages to an external channel.'
);

INSERT OR IGNORE INTO object_epistemic_tags(object_type, object_key, tag_key, note)
VALUES (
    'row',
    'code_artifacts:name=messenger-adapter.telegramm',
    'kind:messenger-adapter',
    'Messenger adapter extension.'
);
