# Skill synonym map — canonical name → list of acceptable aliases
SKILL_SYNONYMS = {
    'javascript': ['js', 'javascript', 'ecmascript', 'es6', 'es2015'],
    'typescript': ['ts', 'typescript'],
    'python': ['python', 'python3', 'py', 'python2'],
    'react': ['react', 'reactjs', 'react.js', 'react native'],
    'vue': ['vue', 'vuejs', 'vue.js'],
    'angular': ['angular', 'angularjs'],
    'django': ['django', 'drf', 'django rest framework'],
    'flask': ['flask', 'flask-restful'],
    'fastapi': ['fastapi', 'fast api'],
    'node': ['node', 'nodejs', 'node.js'],
    'express': ['express', 'expressjs', 'express.js'],
    'postgresql': ['postgresql', 'postgres', 'pg', 'psql'],
    'mysql': ['mysql', 'mariadb'],
    'mongodb': ['mongodb', 'mongo'],
    'redis': ['redis', 'redis cache'],
    'docker': ['docker', 'containerization', 'containers'],
    'kubernetes': ['kubernetes', 'k8s', 'kubectl'],
    'aws': ['aws', 'amazon web services', 'ec2', 's3', 'lambda', 'amazon cloud'],
    'azure': ['azure', 'microsoft azure'],
    'gcp': ['gcp', 'google cloud', 'google cloud platform'],
    'git': ['git', 'github', 'gitlab', 'bitbucket', 'version control'],
    'rest': ['rest', 'rest api', 'restful', 'rest apis', 'restful apis'],
    'graphql': ['graphql', 'gql'],
    'sql': ['sql', 'structured query language'],
    'html': ['html', 'html5'],
    'css': ['css', 'css3', 'scss', 'sass', 'less'],
    'tailwind': ['tailwind', 'tailwindcss', 'tailwind css'],
    'linux': ['linux', 'unix', 'bash', 'shell scripting'],
    'machine learning': ['ml', 'machine learning', 'deep learning', 'ai', 'artificial intelligence'],
    'java': ['java', 'java se', 'java ee'],
    'spring': ['spring', 'spring boot', 'spring framework'],
    'go': ['go', 'golang'],
    'rust': ['rust', 'rust lang'],
    'php': ['php', 'php7', 'php8'],
    'laravel': ['laravel'],
    'ci/cd': ['ci/cd', 'cicd', 'jenkins', 'github actions', 'gitlab ci', 'circleci'],
    'agile': ['agile', 'scrum', 'kanban', 'jira'],
    'figma': ['figma', 'sketch', 'adobe xd', 'ui design'],
    'data analysis': ['data analysis', 'data analytics', 'tableau', 'power bi', 'excel'],
    'pandas': ['pandas', 'numpy', 'scipy'],
    'communication': ['communication', 'written communication', 'verbal communication'],
    'leadership': ['leadership', 'team lead', 'team management'],
    'project management': ['project management', 'pmp', 'prince2'],
}


def normalize_skill(skill: str) -> str:
    """Return canonical skill name from synonym map, or lowercased original."""
    s = skill.lower().strip()
    for canonical, synonyms in SKILL_SYNONYMS.items():
        if s in synonyms or s == canonical:
            return canonical
    return s
