#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright 2017-2018 by Alexis Pietak & Cecil Curry.
# See "LICENSE" for further details.

'''
Low-level **non-pooled worker thread** (i.e., platform-portable, pure-Qt,
:class:`QThread`-based thread wrapper running zero or more subordinate
:class:`QBetseeLoneThreadWorkerABC`-based workers at a given time) classes.
'''

#FIXME: Most (all?) methods defined below are intended to be run *ONLY* from the
#main thread and hence should raise "BetseePySideThreadException" when this is
#*NOT* the case. At the very least, this should be well-documented below.

# ....................{ IMPORTS                            }....................
from PySide2.QtCore import QCoreApplication, QThread
# from betse.util.io.log import logs
from betse.util.type.types import type_check  #, CallableTypes
from betsee.guiexception import BetseePySideThreadException
from betsee.util.thread.lone.guiloneworker import QBetseeLoneThreadWorkerABC

# ....................{ SUPERCLASSES                       }....................
class QBetseeLoneThread(QThread):
    '''
    Low-level **non-pooled worker thread"** (i.e., platform-portable, pure-Qt,
    :class:`QThread`-based wrapper running zero or more subordinate
    :class:`QBetseeLoneThreadWorkerABC`-based workers at a given time).

    Caveats
    ----------
    This obsolete superclass has been superceded by the superior
    :class:`betse.util.thread.pool.guipoolthread.QBetseeThreadPool` superclass,
    whose :class:`QRunnable`-based API requires substantially less boilerplate.

    The *only* methods of this subclass safely callable by external objects are
    the superclass :meth:`start` method and all subclass-specific public methods
    and properties. Other superclass methods (e.g., :meth:`exec`, :meth:`exit`,
    :meth:`quit`, :meth:`run`) should be considered unsafe for external usage
    and hence *never* called externally.

    Design
    ----------
    By design, this subclass intentionally does *not* override the superclass
    :meth:`run` method. While technically feasible (and even sadly encouraged by
    official documentation), doing so invites practical complications that
    *cannot* be trivially circumvented. These include:

    * The inability to run signalled slots of this subclass in this thread.
      Instead, each such slot is run in the thread from which that signal was
      emitted (e.g., the main event-handling thread). This severe constraint
      prohibits this thread from handling signals received from other threads,
      effectively rendering this thread useless for *most* real-world purposes.
    * The need to manually "spin up" a Qt event loop by calling the superclass
      :meth:`exec` method within the subclass :meth:`run` implementation.
    * The need to manually handle the threading lifecycle (e.g., pausing,
      resuming) with error-prone, low-level Qt primitives, including:
      * Mutual exclusions (e.g., :class:`QMutex`, :class:`QSemaphore`).
      * Thread-safe types (e.g., C++-style atomics).

    Instead, this subclass *strongly* recommends that
    :class:`QBetseeLoneThreadWorkerABC`-based workers be moved from the main
    event-handling thread to this thread by the :meth:`adopt_worker` method.

    See Also
    ----------
    https://mayaposch.wordpress.com/2011/11/01/how-to-really-truly-use-qthreads-the-full-explanation
        Blog article on the inadvisability of overriding the :meth:`run` method.
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this worker thread.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # Garbage collect all child objects of this parent thread *AFTER* this
        # thread's event loop and hence execution gracefully terminates (e.g.,
        # by an external call to the halt() method).
        self.finished.connect(self.deleteLater)

    # ..................{ PROPERTIES                         }..................
    @property
    def process_name(self) -> str:
        '''
        Name of the OS-level process associated with this thread, equivalent to
        the Qt-specific name of this object.

        While Qt-specific object names are typically hidden from end users, the
        name of this thread is perhaps surprisingly published to end users
        through the process list for most operating systems (e.g., via the
        external ``ps -L`` command on POSIX-compatible systems).

        This name defaults to the unqualified and largely unreadable name of
        this class (e.g., ``QBetseeLoneThread``). Callers are advised to set
        this property to a human-readable name uniquely identifying this thread
        *before* calling the :meth:`start` method. (Attempting to set this name
        *after* calling that method silently reduces to a noop.)
        '''

        return self.objectName()


    @process_name.setter
    @type_check
    def process_name(self, process_name: str) -> None:
        '''
        Set the name of the OS-level process associated with this thread,
        equivalent to the Qt-specific name of this object, to the passed string.
        '''

        self.setObjectName(process_name)

    # ..................{ HALTERS                            }..................
    @type_check
    def halt(self) -> None:
        '''
        Gracefully terminate this thread.

        Specifically, this method:

        * Gracefully terminates this thread's event loop (i.e., the
          :meth:`exec` method) and hence this thread's execution (i.e., the
          :meth:`run` method).
        * Waits indefinitely for this thread's execution to gracefully
          terminate.

        Caveats
        ----------
        This method does *not* gracefully terminate any adopted worker of this
        thread running in this thread at the time of this call. Rather, such a
        worker will be non-gracefully terminated.

        The :meth:`terminate` method non-gracefully terminating this thread
        should *never* be called for any reason whatsoever. Doing so typically
        disrupts sane thread-safety in a manner inducing application-terminating
        segmentation faults. That's bad.

        The :meth:`exit` method gracefully terminating this thread's event loop
        should *never* be called either. This method's name is poorly chosen and
        bears no relation to actually exiting, quitting, or otherwise
        terminating this thread. Instead, this method merely undoes any prior
        call to the :meth:`exec` method starting this thread's event loop.

        The :meth:`quit` method is a perfect alias of the :meth:`exit` method
        and hence equally inadvisable for external use. Don't call it, either.

        In short, the :class:`QThread` API is a contemptible mess. Avoid it
        wherever possible; complain about it on StackOverflow and Reddit
        wherever impossible.
        '''

        # Gracefully terminate this thread's event loop and hence this thread's
        # execution. This should be the *ONLY* call to this method across the
        # entire codebase.
        self.quit()

        # Wait indefinitely for this thread to gracefully terminate.
        self.wait()

    # ..................{ ADOPTERS                           }..................
    @type_check
    def adopt_worker(self, *workers: QBetseeLoneThreadWorkerABC) -> None:
        '''
        Adopt all passed application-specific workers into this thread.

        Specifically, this method iteratively:

        * Moves each such worker into this thread.
        * Automates the lifecycle of these workers by deleting these workers
          when this thread is deleted.

        This method does *not* classify these workers as instance variables of
        this object. This thread object is technically *not* a thread; this
        thread object is merely a high-level wrapper encapsulating a thread.
        This thread object does *not* reside in this thread but rather in the
        parent thread (e.g., main event-handling thread) in which this object
        was instantiated. This worker *does* reside in this thread after this
        method returns, however. Objects residing in different threads should
        *never* retain references to one another. Ergo, the conclusion follows.

        Caveats
        ----------
        Avoid manually calling the :meth:`QBetseeLoneThreadWorkerABC.moveToThread`
        method to move workers into this thread. Doing so prevents this method
        from automating the lifecycle of these workers -- notably, the guarantee
        that these workers be deleted when this thread is deleted.

        Parameters
        ----------
        workers : tuple[QBetseeLoneThreadWorkerABC]
            Tuple of all workers to be adopted by this thread.
        '''

        # For each such worker...
        for worker in workers:
            # Move this worker into this thread.
            worker.moveToThread(self)

            #FIXME: *NOPE.* While this seems sensible, actually doing this
            #results in the entire application fatally segmentation-faulting
            #without a human-readable exception or error. Ergo, bad. Somehow.

            # Garbage collect all child objects of this worker *AFTER* this
            # thread's event loop and hence execution gracefully terminates
            # (e.g., by an external call to the halt() method).
            # self.finished.connect(worker.deleteLater)

# ....................{ SUPERCLASSES ~ single              }....................
class QBetseeLoneSingleThread(QBetseeLoneThread):
    '''
    Low-level **non-pooled single worker thread"** (i.e., platform-portable,
    pure-Qt, :class:`QThread`-based thread wrapper, confined to run a single
    subordinate :class:`QBetseeLoneThreadWorkerABC`-based worker at a given
    time).

    By default, both the standard :class:`QThread` class and our
    :class:`QBetseeLoneThread` superclass implicitly allow a one-to-many
    relation between a parent thread and its child workers such that a single
    thread may run an arbitrary number of (i.e., zero or more) workers.

    Attributes
    ----------
    _is_worker : bool
        ``True`` only if this thread has adopted a worker (i.e., the
        :meth:`adopt_worker` method has been called more recently than the
        :meth:`unadopt_worker` method).
    '''

    # ..................{ INITIALIZERS                       }..................
    def __init__(self, *args, **kwargs) -> None:
        '''
        Initialize this single worker thread.
        '''

        # Initialize our superclass with all passed parameters.
        super().__init__(*args, **kwargs)

        # By default, this thread has no adopted worker.
        self._is_worker = False

    # ..................{ PROPERTIES                         }..................
    # Read-only properties.

    @property
    def is_worker(self) -> bool:
        '''
        ``True`` only if this thread has already adopted a worker (i.e., the
        :meth:`adopt_worker` method has been called more recently than the
        :meth:`unadopt_worker` method).
        '''

        return self._is_worker

    # ..................{ EXCEPTIONS                         }..................
    def _die_if_worker(self) -> None:
        '''
        Raise an exception if this thread has already adopted a worker.

        Raises
        ----------
        BetseePySideThreadException
            If this thread has already adopted a worker.

        See Also
        ----------
        :meth:`is_worker`
            Further details.
        '''

        # If this thread has already adopted a worker, raise an exception.
        if self.is_worker:
            raise BetseePySideThreadException(QCoreApplication.translate(
                'QBetseeWorkerSingleThread',
                'Worker already adopted by this thread.'))


    def _die_unless_worker(self) -> None:
        '''
        Raise an exception if unless thread has already adopted a worker (i.e.,
        if this thread has adopted no worker).

        Raises
        ----------
        BetseePySideThreadException
            If this thread has adopted no worker.

        See Also
        ----------
        :meth:`is_worker`
            Further details.
        '''

        # If this thread has adopted no worker, raise an exception.
        if not self.is_worker:
            raise BetseePySideThreadException(QCoreApplication.translate(
                'QBetseeWorkerSingleThread',
                'No worker adopted by this thread.'))

    # ..................{ HALTERS                            }..................
    @type_check
    def halt(self) -> None:
        '''
        Gracefully terminate this thread.

        Specifically, this method:

        * If this thread has adopted a worker, unadopts this worker. Doing so
          ensures exceptions are raised in the common edge case that this worker
          is still running.
        * Gracefully terminates this thread's event loop (i.e., the
          :meth:`exec` method) and hence this thread's execution (i.e., the
          :meth:`run` method).
        * Waits indefinitely for this thread's execution to gracefully
          terminate.

        Caveats
        ----------
        This method does *not* gracefully terminate any adopted worker of this
        thread running in this thread at the time of this call. Rather, such a
        worker will be non-gracefully terminated.

        The :meth:`terminate` method non-gracefully terminating this thread
        should *never* be called for any reason whatsoever. Doing so typically
        disrupts sane thread-safety in a manner inducing application-terminating
        segmentation faults. That's bad.

        The :meth:`exit` method gracefully terminating this thread's event loop
        should *never* be called either. This method's name is poorly chosen and
        bears no relation to actually exiting, quitting, or otherwise
        terminating this thread. Instead, this method merely undoes any prior
        call to the :meth:`exec` method starting this thread's event loop.

        The :meth:`quit` method is a perfect alias of the :meth:`exit` method
        and hence equally inadvisable for external use. Don't call it, either.

        In short, the :class:`QThread` API is a contemptible mess. Avoid it
        wherever possible; complain about it on StackOverflow and Reddit
        wherever impossible.
        '''

        # If this thread has adopted a worker, unadopt this worker *BEFORE*
        # calling the superclass method, which terminates this thread. Doing so
        # ensures exceptions are raised in the common edge case that this worker
        # is still running.
        if self.is_worker:
            self.unadopt_worker()

        # Gracefully terminate this thread.
        super().halt()

    # ..................{ ADOPTERS                           }..................
    @type_check
    def adopt_worker(self, *workers: QBetseeLoneThreadWorkerABC) -> None:
        '''
        Adopt all passed application-specific workers into this thread if no
        other worker has already been adopted by this thread *or* raise an
        exception otherwise (i.e., if this thread has already adopted a worker).

        Specifically, this method iteratively:

        * Moves each such worker into this thread while preserving the
          guarantees contractually stipulated by this thread -- notably, that
          this thread run one and *only* one worker at a time.

        Design
        ----------
        For safety, this method does *not* classify this worker as an instance
        variable of this object. Why? Because this object is technically *not* a
        thread; this object is merely a high-level wrapper encapsulating a
        thread. This object does *not* reside in this thread but rather in the
        parent thread (e.g., main event-handling thread) in which this object
        was instantiated. This worker *does* reside in this thread after this
        method returns, however. Objects residing in different threads should
        *never* retain references to one another. Ergo, the conclusion follows.

        Instead, this method merely classifies an arbitrary worker to have now
        been adopted by this thread via the :meth:`is_worker` property.

        Caveats
        ----------
        The :meth:`QBetseeLoneThreadWorkerABC.moveToThread` method should
        *never* be called to manually move a worker into this thread. Doing so
        violates subclass encapsulation and hence the guarantee that this thread
        run *only* a single worker at a time.
        '''

        # If this thread has already adopted a worker, raise an exception.
        self._die_if_worker()

        # Move this worker to this thread.
        super().adopt_worker(workers)

        #FIXME: Connect appropriate signals and slots... after defining them. In
        #particular, at least:
        #
        #* Augment the unadopt_worker() method into a slot.
        #* Connect the worker.halt() signal to the unadopt_worker() slot.

        # Record this thread as having a worker *AFTER* successfully doing so.
        self._is_worker = True


    #FIXME: This method should explicitly handle the common edge case of an
    #adopted worker that is still running by detecting this edge case and
    #either:
    #
    #* Raising an exception. (Non-ideal, but acceptable.)
    #* Emitting a signal connected to the halt() slot of this worker,
    #  instructing this worker to gracefully shutdown. While preferable,
    #  implementing this logic is presumably complicated by the need for this
    #  thread to wait for this slot to return before terminating this thread.
    def unadopt_worker(self) -> None:
        '''
        Unadopt the passed application-specific worker from this thread if a
        worker has already been adopted by this thread *or* raise an exception
        otherwise (i.e., if this thread has adopted no such worker).
        '''

        # If this thread has adopted no such worker, raise an exception.
        self._die_unless_worker()

        #FIXME: Do something appropriate here. Maybe emit appropriate signals?

        # Record this thread as having no worker *AFTER* successfully doing so.
        self._is_worker = False
