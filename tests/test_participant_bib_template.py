from pathlib import Path


def test_participant_bib_template_has_print_layouts_and_editable_fields():
    template = (
        Path(__file__).parents[1]
        / 'templates'
        / 'reports'
        / '3_номера_участников.html'
    ).read_text(encoding='utf-8')

    assert '@page { size: A4 landscape; margin: 0; }' in template
    assert 'width: 297mm; height: 210mm' in template
    assert 'layout-1' in template
    assert 'layout-2' in template
    assert 'layout-4' in template
    assert "node.contentEditable = 'true'" in template
    assert 'Number(person.bib || 0) > 0' in template
