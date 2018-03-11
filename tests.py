import pytest
from lxml import etree


class Testlxml():
    def test_parse(self):
        root = etree.parse('files/sample.xml')

        # etree.parse() returns an _ElementTree.
        assert isinstance(root, etree._ElementTree)

        # We can get the root _Element using getroot().
        assert isinstance(root.getroot(), etree._Element)

    def test_fromstring(self):
        root = etree.fromstring('<record><foo>bar</foo></record>')

        # When converting from string, an _Element is returned. This differs from etree.parse().
        assert isinstance(root, etree._Element)

        # It's possible to convert an _Element to an _ElementTree.
        assert isinstance(root.getroottree(), etree._ElementTree)
        assert isinstance(etree.ElementTree(root), etree._ElementTree)

    def test_encoding(self):
        reference = etree.parse('files/incorrect_encoding_reference.xml')

        # If the source file has an incorrect XML declaration, the contents will be incorrectly encoded.
        incorrect_encoding = etree.parse('files/incorrect_encoding.xml')
        assert etree.tostring(incorrect_encoding) != etree.tostring(reference)

        # We can override the automatic encoding discovery to force etree.parse() to read the file correctly.
        parser = etree.XMLParser(encoding='utf8')
        correct_encoding = etree.parse('files/incorrect_encoding.xml', parser=parser)
        assert etree.tostring(correct_encoding) == etree.tostring(reference)

    def test_build_xml(self):
        el = etree.Element('foo', name='bar')
        el.text = 'Hello'
        assert etree.tostring(el) == b'<foo name="bar">Hello</foo>'

        subel = etree.SubElement(el, 'baz')
        subel.text = 'World'
        assert etree.tostring(subel) == b'<baz>World</baz>'
        assert etree.tostring(el) == b'<foo name="bar">Hello<baz>World</baz></foo>'

        subel2 = etree.Element('qux')
        subel2.text = 'There'
        el.insert(0, subel2)
        assert etree.tostring(subel2) == b'<qux>There</qux>'
        assert etree.tostring(el) == b'<foo name="bar">Hello<qux>There</qux><baz>World</baz></foo>'

    def test_prepend_element(self):
        el = etree.Element('foo')
        el.text = 'World'
        assert etree.tostring(el) == b'<foo>World</foo>'

        subel = etree.SubElement(el, 'baz')
        subel.text = 'Hello'
        subel.tail = el.text
        el.text = None
        assert etree.tostring(subel) == b'<baz>Hello</baz>World'
        assert etree.tostring(el) == b'<foo><baz>Hello</baz>World</foo>'

    def test_namespaces(self):
        root = etree.parse('files/sample.xml')

        # Using the selector without a namespace will only find the non-namespaced element.
        assert len(root.findall('foo')) == 1
        assert len(root.xpath('//foo')) == 1

        # Trying to find an element in an unknown namespace will raise a SyntaxError.
        with pytest.raises(SyntaxError):
            root.findall('xmlfoo:foo')

        # Trying to use an unknown namespace in an XPath selector will raise an XPathEvalError.
        with pytest.raises(etree.XPathEvalError):
            root.xpath('//xmlfoo:foo')

        # Unfortunately XPathEvalError doesn't subclass SyntaxError; it inherits from LxmlError via XPathError.
        assert not issubclass(etree.XPathEvalError, SyntaxError)
        assert issubclass(etree.XPathEvalError, etree.XPathError)
        assert issubclass(etree.XPathError, etree.LxmlError)

        # Clark notation can be used in find, findall, iter, and iterfind.
        assert len(root.findall('{http://example.com}foo')) == 1
        assert len(root.findall('{*}foo')) == 2

        # This can't be used with XPath since it's not a valid selector. Instead, we can use a wildcard with a filter.
        # This will be very slow for large XML structures since it has to check every element. Always prefer mappings.
        assert len(root.xpath('//*[local-name(.) = "foo"]')) == 2
        assert len(root.xpath('//*[local-name(.) = "foo" and namespace-uri() = "http://example.com"]')) == 1

        # The wildcard namespace selector is only valid for XPath 2.0, which is not currently supported by libxml2.
        with pytest.raises(etree.XPathEvalError):
            root.xpath('//*:foo')

        nsmap = {
            'xmlfoo': 'http://example.com',
        }

        # Once we supply the namespace mapping, we can use both findall() and xpath() with the namespaced selector.
        assert len(root.findall('xmlfoo:foo', namespaces=nsmap)) == 1
        assert len(root.xpath('//xmlfoo:foo', namespaces=nsmap)) == 1

