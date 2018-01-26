#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Abstract base classes of all editable enumerative simulation configuration
widget subclasses instantiated in pages of the top-level stack.
'''

#FIXME: Don't neglect to submit our "uiparser.py" fix to upstream! Nargle!

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, QObject  #, Signal, Slot
# from betse.util.io.log import logs
from betse.util.type.mapping import mappings
from betse.util.type.types import (
    type_check, ClassOrNoneTypes, EnumClassType, MappingType)
from betsee.guiexception import BetseePySideWidgetEnumException
from betsee.gui.simconf.stack.widget.abc.guisimconfwdgeditscalar import (
    QBetseeSimConfEditScalarWidgetMixin)

# ....................{ MIXINS                             }....................
class QBetseeSimConfEditEnumWidgetMixin(QBetseeSimConfEditScalarWidgetMixin):
    '''
    Abstract base class of all **editable enumerative simulation configuration
    widget** (i.e., widget interactively selecting between the mutually
    exclusive members of a simulation configuration enumeration stored in
    external YAML files) subclasses.

    Attributes
    ----------
    _enum_member_to_widget_value : MappingType
        Dictionary mapping from each member of the enumeration constraining this
        widget to the corresponding mutually exclusive value displayed by this
        widget.
    _widget_value_to_enum_member : MappingType
        Dictionary mapping from each mutually exclusive value displayed by this
        widget to the corresponding member of the enumeration constraining this
        widget.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:

        # Initialize our superclass with all passed arguments.
        super().__init__(*args, **kwargs)

        # Nullify all instance variables for safety.
        self._enum_member_to_widget_value = None
        self._widget_value_to_enum_member = None


    @type_check
    def init(
        self, enum_member_to_widget_value: MappingType, *args, **kwargs
    ) -> None:
        '''
        Finalize the initialization of this widget.

        Parameters
        ----------
        enum_member_to_widget_value : MappingType
            Dictionary mapping from each member of the enumeration encapsulated
            by the passed ``sim_conf_alias`` parameter to the corresponding
            mutually exclusive value displayed by this widget.

        All remaining parameters are passed as is to the superclass method.

        Raises
        ----------
        BetseMappingException
            If this dictionary is *not* safely invertible (i.e., if any value of
            this dictionary is non-uniquely assigned to two or more keys).
        BetseePySideRadioButtonException
            If the number of members in this enumeration differs from the number
            of members mapped by (i.e., of keys in) this dictionary.
        '''

        # Initialize our superclass with all remaining parameters.
        super().init(*args, **kwargs)

        # Classify both this dictionary and its inverse.
        self._enum_member_to_widget_value = enum_member_to_widget_value
        self._widget_value_to_enum_member = mappings.invert_map_unique(
            enum_member_to_widget_value)
        # logs.log_debug('enum_member_to_widget_value: {!r}'.format(
        #     self._enum_member_to_widget_value))
        # logs.log_debug('widget_value_to_enum_member: {!r}'.format(
        #     self._widget_value_to_enum_member))

        # Enumeration constraining this simulation configuration alias. Note
        # that this type need *NOT* validated here, as the
        # _sim_conf_alias_type_strict() property instructs our superclass to do
        # so already.
        enum_type = self._sim_conf_alias.data_desc.expr_alias_cls

        # If the number of members in this enumeration differs from the number
        # of members mapped by this dictionary, raise an exception.
        if len(enum_type) != len(enum_member_to_widget_value):
            raise BetseePySideWidgetEnumException(QCoreApplication.translate(
                'QBetseeSimConfEditEnumWidgetMixin',
                'Number of enumeration members {0} differs from '
                'number of mapped enumeration members {1}.'.format(
                    len(enum_type), len(enum_member_to_widget_value))))

    # ..................{ PROPERTIES                         }..................
    @property
    def _sim_conf_alias_type_strict(self) -> ClassOrNoneTypes:

        # Enumeration types are subclasses of the "EnumClassType" superclass and
        # instances of the "EnumType" type. Since the superclass
        # _die_if_sim_conf_alias_type_invalid() method validates types with
        # issubclass() rather than isinstance(), the former type is returned.
        return EnumClassType

    # ..................{ GETTERS                            }..................
    def _get_alias_from_widget_value(self) -> object:

        # Currently displayed value of this widget.
        widget_value = self.widget_value

        # If this value corresponds to no enumeration member, raise an
        # exception. While this should *NEVER* be the case, should should never
        # be a word.
        if widget_value not in self._widget_value_to_enum_member:
            # Human-readable description of this value.
            widget_value_label = widget_value

            # If this value is a Qt-specific object, reduce this description to
            # this object's name.
            if isinstance(widget_value, QObject):
                widget_value_label = widget_value.objectName()

            # Raise this exception with this description.
            raise BetseePySideWidgetEnumException(QCoreApplication.translate(
                'QBetseeSimConfEditEnumWidgetMixin',
                'Widget value "{0}" unrecognized.'.format(
                    widget_value_label)))

        # Return the enumeration member corresponding to this button.
        return self._widget_value_to_enum_member[widget_value]


    def _get_widget_from_alias_value(self) -> object:

        # Current value of this simulation configuration alias.
        enum_member = self._sim_conf_alias.get()

        # If this is *NOT* a member of this enumeration, raise an exception.
        # While this should *NEVER* be the case, should should never be a word.
        if enum_member not in self._enum_member_to_widget_value:
            raise BetseePySideWidgetEnumException(QCoreApplication.translate(
                'QBetseeSimConfEditEnumWidgetMixin',
                'Enumeration member "{0}" unrecognized.'.format(
                    str(enum_member))))

        # Return the radio button corresponding to this member.
        return self._enum_member_to_widget_value[enum_member]
