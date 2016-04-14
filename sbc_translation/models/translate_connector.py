# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import datetime

from openerp.addons.mysql_connector.model.mysql_connector \
    import mysql_connector


class TranslateConnect(mysql_connector):
    """ Contains all the utility methods needed to talk with the MySQL server
        used by translate platform, as well as all mappings
        from OpenERP fields to corresponding MySQL fields.
    """

    def __init__(self):
        super(TranslateConnect, self).__init__(
            'mysql_translate_host',
            'mysql_translate_user',
            'mysql_translate_pw',
            'mysql_translate_db')

        self.current_time = datetime.datetime.now()

    def upsert_text(self, correspondence, file_name,
                    src_lang_id, dst_lang_iso):
        """Push or update text (db table) on local translate platform
        """
        child = correspondence.child_id
        sponsor = correspondence.correspondant_id

        self.letter_name = file_name
        child_age = datetime.date.today().year - int(child.birthdate[:4])

        text_type_id = 2 if correspondence.direction ==\
            'Supporter To Beneficiary' else 1

        vals = {
            'src_lang_id': src_lang_id,
            'aim_lang_id': dst_lang_iso,
            'title': self.letter_name,
            'file': self.letter_name,
            'codega': sponsor.ref,
            'gender': sponsor.title.name,
            'name': sponsor.name,
            'firstname': sponsor.firstname,
            'code': child.code,
            'kid_name': child.name,
            'kid_firstname': child.firstname,
            'age': child_age,
            'kid_gender': child.gender,
            'createdat': self.current_time,
            'updatedat': self.current_time,
            'priority_id': 1,  # Not urgent, default
            'text_type_id': text_type_id,
        }
        return self.upsert("text", vals)

    def upsert_translation(self, text_id, letter):
        """Push or update translation (db table) on local translate platform
        """

        vals = {
            'file': self.letter_name[0:-4] + '.rtf',
            'text_id': text_id,
            'createdat': self.current_time,
            'updatedat': self.current_time,
            'toDo_id': 0,
            'letter_odoo_id': letter.id,
        }
        return self.upsert("translation", vals)

    def upsert_translation_status(self, translation_id):
        """Push or update translation_status (db table) on local translate
        platform
        """
        to_translate = 1
        vals = {
            'translation_id': translation_id,
            'status_id': to_translate,
            'createdat': self.current_time,
            'updatedat': self.current_time,
        }
        return self.upsert("translation_status", vals)

    def get_lang_id(self, lang_compassion_id):
        """ Returns the language's id in MySQL that has  GP_Libel pointing
         to the iso_code given (returns -1 if not found). """
        res = self.selectOne(
            "SELECT id FROM language WHERE GP_Libel LIKE '{}'"
            .format(lang_compassion_id.code_iso))
        return res['id'] if res else -1

    def get_translated_letters(self):
        """ Returns a list for dictionaries with translation and filename
        (sponsorship_id is in the file name...) in MySQL translation_test
        database that has translation_status to 'Traduit" (id = 3)
        (returns -1 if not found). """
        res = self.selectAll(
            "SELECT tr.id, tr.letter_odoo_id, tr.text, l.GP_libel target_lang\
            FROM translation_status trs\
            INNER JOIN translation tr\
            ON trs.translation_id = tr.id\
            INNER JOIN text txt\
            ON tr.text_id = txt.id\
            INNER JOIN language l\
            ON txt.aim_lang_id = l.id\
            WHERE tr.letter_odoo_id IS NOT NULL\
            AND trs.status_id = 3"
        )
        return res

    def remove_letter(self, id):
        """ Delete a letter record with the translation_id given """
        self.remove_from_translation_status(id)
        text_id = self.remove_from_translation(id)
        self.remove_from_text(text_id)

    def remove_from_translation_status(self, id):
        """ Delete a translation_status record for the translation_id given """
        self.query("DELETE FROM translation_status WHERE translation_id={}"
                   .format(id))

    def remove_from_translation(self, id):
        """ Delete a translation record for the translation_id given
            Return the text_id corresponding to this record"""
        res = self.selectOne("SELECT text_id FROM translation WHERE id={}"
                             .format(id))
        self.query("DELETE FROM translation WHERE id={}"
                   .format(id))
        return res['text_id']

    def remove_from_text(self, id):
        """ Delete a text record for the text_id given """
        self.query("DELETE FROM text WHERE id={}"
                   .format(id))
