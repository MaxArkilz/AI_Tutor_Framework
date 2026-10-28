import { useEffect, useState } from 'react';
import { createBrowserRouter, Outlet } from 'react-router-dom';
import type { RouteObject } from 'react-router-dom';
import Home from './pages/home';
import NotFound from './pages/404';
import axios from 'axios';
import BYUHeader from './components/byuHeader';
import EarlModal from './components/earlModal';
import {PrepExam, AlgebraHelp, Notes, PracticeProblems, StudyGuide, VisualTools, History} from './pages/index';
import ClassLanding from './pages/classes/classLanding';
import ClassDetail from './pages/classes/classDetail';
import { useTitle } from './hooks/useTitle';

const routes: RouteObject[] = [
    {
        path: '/',
        element: (
            <div>
                <BYUHeader />
                <main>
                    <Outlet />
                </main>
                <EarlModal />
            </div>
        ),
        errorElement: <NotFound />,
        children: [
            { index: true, element: <Home />},
            { path: 'classes', element: <ClassLanding />},
            { path: 'classes/:classCode', element: <ClassDetail />},
            { path: 'prep_exam', element: <PrepExam />},
            { path: 'practice', element: <PracticeProblems />},
            { path: 'tools', element: <VisualTools />},
            { path: 'notes', element: <Notes /> },
            { path: 'math', element: <AlgebraHelp /> },
            { path: 'study', element: <StudyGuide />},
            { path: 'past', element: <History />},
        ]
    }
]

export const AppRoutes = createBrowserRouter(routes);
